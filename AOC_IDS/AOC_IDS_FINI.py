import torch
import numpy as np
import pandas as pd
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import TensorDataset
from sklearn.model_selection import train_test_split
from utils import *

import argparse
import warnings

warnings.filterwarnings('ignore')

# =============================================================================
# ARGUMENTS
# =============================================================================

parser = argparse.ArgumentParser(description='AOC-IDS')
parser.add_argument("--dataset", type=str, default='nsl')
parser.add_argument("--epochs", type=int, default=4)
parser.add_argument("--epoch_1", type=int, default=1)
parser.add_argument("--percent", type=float, default=0.8)
parser.add_argument("--flip_percent", type=float, default=0.2)
parser.add_argument("--sample_interval", type=int, default=2000)
parser.add_argument("--cuda", type=str, default="0")
parser.add_argument("--train_path", type=str, default=None)
parser.add_argument("--test_path", type=str, default=None)
parser.add_argument("--output_path", type=str, default="./anomalies_detected.csv")

args = parser.parse_args()
dataset = args.dataset
epochs = args.epochs
epoch_1 = args.epoch_1
percent = args.percent
flip_percent = args.flip_percent
sample_interval = args.sample_interval
cuda_num = args.cuda

tem = 0.02
bs = 128
seed = 5009
seed_round = 5

# =============================================================================
# CLASSES
# =============================================================================

class SplitData(BaseEstimator, TransformerMixin):
    def __init__(self, dataset):
        super(SplitData, self).__init__()
        self.dataset = dataset

    def fit(self, X, y=None):
        return self 
    
    def transform(self, X, labels, one_hot_label=True):
        if self.dataset == 'nsl':
            y = X[labels]
            X_ = X.drop(['labels5', 'labels2'], axis=1)
            y = (y != 'normal')
            y_ = np.asarray(y).astype('float32')

        elif self.dataset == 'unsw':
            y_ = X[labels]
            X_ = X.drop('label', axis=1)

        elif self.dataset == 'netmob':
            y_ = X[labels].values
            cols_to_drop = ['label']
            for col in ['date', 'tile_id', 'service']:
                if col in X.columns:
                    cols_to_drop.append(col)
            X_ = X.drop(cols_to_drop, axis=1)
            X_ = X_.apply(pd.to_numeric, errors='coerce').fillna(0)
            y_ = np.asarray(y_).astype('float32')

        else:
            raise ValueError("Unsupported dataset type")

        normalize = MinMaxScaler().fit(X_)
        x_ = normalize.transform(X_)

        return x_, y_


def description(data):
    print("Number of samples(examples) ", data.shape[0], " Number of features", data.shape[1])
    print("Dimension of data set ", data.shape)


class AE(nn.Module):
    def __init__(self, input_dim):
        super(AE, self).__init__()

        nearest_power_of_2 = 2 ** round(math.log2(input_dim))
        second_fourth_layer_size = nearest_power_of_2 // 2
        third_layer_size = nearest_power_of_2 // 4

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, second_fourth_layer_size),
            nn.ReLU(),
            nn.Linear(second_fourth_layer_size, third_layer_size),
        )

        self.decoder = nn.Sequential(
            nn.ReLU(),
            nn.Linear(third_layer_size, second_fourth_layer_size),
            nn.ReLU(),
            nn.Linear(second_fourth_layer_size, input_dim),
        )

    def forward(self, x):
        encode = self.encoder(x)
        decode = self.decoder(encode)
        return encode, decode


class CRCLoss(nn.Module):
    def __init__(self, device, temperature=0.1, scale_by_temperature=True):
        super(CRCLoss, self).__init__()
        self.device = device
        self.temperature = temperature
        self.scale_by_temperature = scale_by_temperature

    def forward(self, features, labels=None, mask=None):        
        features = F.normalize(features, p=2, dim=1)
        batch_size = features.shape[0]
        labels = labels.contiguous().view(-1, 1)
        if labels.shape[0] != batch_size:
            raise ValueError('Num of labels does not match num of features')
        mask = torch.eq(labels, labels.T).float()
        logits = torch.div(
            torch.matmul(features, features.T),
            self.temperature)
        logits_mask = torch.ones_like(mask).to(self.device) - torch.eye(batch_size).to(self.device)  
        logits_without_ii = logits * logits_mask
        
        logits_normal = logits_without_ii[(labels == 0).squeeze()]
        logits_normal_normal = logits_normal[:,(labels == 0).squeeze()]
        logits_normal_abnormal = logits_normal[:,(labels > 0).squeeze()]
        
        sum_of_vium = torch.sum(torch.exp(logits_normal_abnormal))
        denominator = torch.exp(logits_normal_normal) + sum_of_vium
        log_probs = logits_normal_normal - torch.log(denominator)
  
        loss = -log_probs
        if self.scale_by_temperature:
            loss *= self.temperature
        loss = loss.mean()
        return loss

# =============================================================================
# FONCTIONS
# =============================================================================

def score_detail(y_test, y_test_pred, if_print=False):
    if if_print == True:
        print("Confusion matrix")
        print(confusion_matrix(y_test, y_test_pred))
        print('Accuracy ', accuracy_score(y_test, y_test_pred))
        print('Precision ', precision_score(y_test, y_test_pred))
        print('Recall ', recall_score(y_test, y_test_pred))
        print('F1 score ', f1_score(y_test, y_test_pred))

    return accuracy_score(y_test, y_test_pred), precision_score(y_test, y_test_pred), recall_score(y_test, y_test_pred), f1_score(y_test, y_test_pred)


def setup_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)
    torch.backends.cudnn.deterministic = True


def gaussian_pdf(x, mu, sigma):
    return (1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def log_likelihood(params, data):
    mu1, sigma1, mu2, sigma2 = params
    pdf1 = gaussian_pdf(data, mu1, sigma1)
    pdf2 = gaussian_pdf(data, mu2, sigma2)
    return -np.sum(np.log(0.5 * pdf1 + 0.5 * pdf2))


def evaluate(normal_temp, normal_recon_temp, x_train, y_train, x_test, y_test, model, get_confidence=False, en_or_de=False):
    num_of_layer = 0

    x_train_normal = x_train[(y_train == 0).squeeze()]
    x_train_abnormal = x_train[(y_train == 1).squeeze()]

    train_features = F.normalize(model(x_train)[num_of_layer], p=2, dim=1)
    train_features_normal = F.normalize(model(x_train_normal)[num_of_layer], p=2, dim=1)
    train_features_abnormal = F.normalize(model(x_train_abnormal)[num_of_layer], p=2, dim=1)
    test_features = F.normalize(model(x_test)[num_of_layer], p=2, dim=1)

    values_features_all, indcies = torch.sort(F.cosine_similarity(train_features, normal_temp.reshape([-1, normal_temp.shape[0]]), dim=1))
    values_features_normal, indcies = torch.sort(F.cosine_similarity(train_features_normal, normal_temp.reshape([-1, normal_temp.shape[0]]), dim=1))
    values_features_abnormal, indcies = torch.sort(F.cosine_similarity(train_features_abnormal, normal_temp.reshape([-1, normal_temp.shape[0]]), dim=1))

    values_features_all = values_features_all.cpu().detach().numpy()

    values_features_test = F.cosine_similarity(test_features, normal_temp.reshape([-1, normal_temp.shape[0]]))

    num_of_output = 1
    train_recon = F.normalize(model(x_train)[num_of_output], p=2, dim=1)
    train_recon_normal = F.normalize(model(x_train_normal)[num_of_output], p=2, dim=1)
    train_recon_abnormal = F.normalize(model(x_train_abnormal)[num_of_output], p=2, dim=1)
    test_recon = F.normalize(model(x_test)[num_of_output], p=2, dim=1)

    values_recon_all, indcies = torch.sort(F.cosine_similarity(train_recon, normal_recon_temp.reshape([-1, normal_recon_temp.shape[0]]), dim=1))
    values_recon_normal, indcies = torch.sort(F.cosine_similarity(train_recon_normal, normal_recon_temp.reshape([-1, normal_recon_temp.shape[0]]), dim=1))
    values_recon_abnormal, indcies = torch.sort(F.cosine_similarity(train_recon_abnormal, normal_recon_temp.reshape([-1, normal_recon_temp.shape[0]]), dim=1))

    values_recon_all = values_recon_all.cpu().detach().numpy()

    values_recon_test = F.cosine_similarity(test_recon, normal_recon_temp.reshape([-1, normal_recon_temp.shape[0]]), dim=1)

    mu1_initial = np.mean(values_features_normal.cpu().detach().numpy())
    sigma1_initial = np.std(values_features_normal.cpu().detach().numpy())

    mu2_initial = np.mean(values_features_abnormal.cpu().detach().numpy())
    sigma2_initial = np.std(values_features_abnormal.cpu().detach().numpy())

    initial_params = np.array([mu1_initial, sigma1_initial, mu2_initial, sigma2_initial])
    result = opt.minimize(log_likelihood, initial_params, args=(values_features_all,), method='Nelder-Mead')
    mu1_fit, sigma1_fit, mu2_fit, sigma2_fit = result.x

    if mu1_fit > mu2_fit:
        gaussian1 = dist.Normal(mu1_fit, sigma1_fit)
        gaussian2 = dist.Normal(mu2_fit, sigma2_fit)
    else:
        gaussian2 = dist.Normal(mu1_fit, sigma1_fit)
        gaussian1 = dist.Normal(mu2_fit, sigma2_fit)

    pdf1 = gaussian1.log_prob(values_features_test).exp()
    pdf2 = gaussian2.log_prob(values_features_test).exp()
    y_test_pred_2 = (pdf2 > pdf1).cpu().numpy().astype("int32")
    y_test_pro_en = (torch.abs(pdf2-pdf1)).cpu().detach().numpy().astype("float32")

    if isinstance(y_test, int) == False:
        if y_test.device != torch.device("cpu"):
            y_test = y_test.cpu().numpy()

    mu3_initial = np.mean(values_recon_normal.cpu().detach().numpy())
    sigma3_initial = np.std(values_recon_normal.cpu().detach().numpy())

    mu4_initial = np.mean(values_recon_abnormal.cpu().detach().numpy())
    sigma4_initial = np.std(values_recon_abnormal.cpu().detach().numpy())

    initial_params = np.array([mu3_initial, sigma3_initial, mu4_initial, sigma4_initial])
    result = opt.minimize(log_likelihood, initial_params, args=(values_recon_all,), method='Nelder-Mead')
    mu3_fit, sigma3_fit, mu4_fit, sigma4_fit = result.x

    if mu3_fit > mu4_fit:
        gaussian3 = dist.Normal(mu3_fit, sigma3_fit)
        gaussian4 = dist.Normal(mu4_fit, sigma4_fit)
    else:
        gaussian4 = dist.Normal(mu3_fit, sigma3_fit)
        gaussian3 = dist.Normal(mu4_fit, sigma4_fit)

    pdf3 = gaussian3.log_prob(values_recon_test).exp()
    pdf4 = gaussian4.log_prob(values_recon_test).exp()
    y_test_pred_4 = (pdf4 > pdf3).cpu().numpy().astype("int32")
    y_test_pro_de = (torch.abs(pdf4-pdf3)).cpu().detach().numpy().astype("float32")

    if not isinstance(y_test, int):
        if y_test.device != torch.device("cpu"):
            y_test = y_test.cpu().numpy()
        result_encoder = score_detail(y_test, y_test_pred_2)
        result_decoder = score_detail(y_test, y_test_pred_4)

    y_test_pred_no_vote = torch.where(torch.from_numpy(y_test_pro_en) > torch.from_numpy(y_test_pro_de), torch.from_numpy(y_test_pred_2), torch.from_numpy(y_test_pred_4))
    
    if not isinstance(y_test, int):
        result_final = score_detail(y_test, y_test_pred_no_vote, if_print=True)
        return result_encoder, result_decoder, result_final
    else:
        return y_test_pred_no_vote


# =============================================================================
# CHARGEMENT DES DONNEES
# =============================================================================

print("=" * 60)
print("AOC-IDS")
print("=" * 60)
print(f"Dataset: {dataset}")
print(f"Epochs: {epochs}")

# Variable pour stocker les metadonnees (netmob uniquement)
test_metadata = None

if dataset == 'nsl':
    input_dim = 121

    KDDTrain = pd.read_csv('KDDTrain.csv')
    KDDTest = pd.read_csv('KDDTest.csv')

    splitter = SplitData(dataset='nsl')
    x_train, y_train = splitter.transform(KDDTrain, labels='labels2')
    x_test, y_test = splitter.transform(KDDTest, labels='labels2')


elif dataset == 'unsw':
    input_dim = 196

    UNSWTrain = pd.read_csv('UNSWTrain.csv')
    UNSWTest = pd.read_csv('UNSWTest.csv')

    splitter = SplitData(dataset='unsw')
    x_train, y_train = splitter.transform(UNSWTrain, labels='label')
    x_test, y_test = splitter.transform(UNSWTest, labels='label')


elif dataset == 'netmob':
    input_dim = 15

    if args.train_path is None or args.test_path is None:
        raise ValueError(
            "For dataset='netmob', --train_path and --test_path are REQUIRED"
        )

    print(f"[INFO] Loading NetMob train: {args.train_path}")
    print(f"[INFO] Loading NetMob test : {args.test_path}")

    NetMobTrain = pd.read_csv(args.train_path)
    NetMobTest = pd.read_csv(args.test_path)

    # Garder les metadonnees pour l'export final
    test_metadata = NetMobTest[['tile_id', 'date']].copy()

    splitter = SplitData(dataset='netmob')
    x_train, y_train = splitter.transform(NetMobTrain, labels='label')
    x_test, y_test = splitter.transform(NetMobTest, labels='label')

    print(f"Train: {x_train.shape[0]} samples")
    print(f"Test: {x_test.shape[0]} samples")


else:
    raise ValueError(f"Unknown dataset: {dataset}")

print("=" * 60)

# Convert to torch tensors
x_train, y_train = torch.FloatTensor(x_train), torch.LongTensor(y_train)
x_test, y_test = torch.FloatTensor(x_test), torch.LongTensor(y_test)

device = torch.device("cuda:"+cuda_num if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

criterion = CRCLoss(device, tem)

# =============================================================================
# ENTRAINEMENT
# =============================================================================

for i in range(seed_round):
    setup_seed(seed+i)
    print(f"\n[Round {i+1}/{seed_round}] seed = {seed+i}")

    online_x_train, online_x_test, online_y_train, online_y_test = train_test_split(x_train, y_train, test_size=percent, random_state=seed+i)
    train_ds = TensorDataset(online_x_train, online_y_train)
    train_loader = torch.utils.data.DataLoader(
        dataset=train_ds, batch_size=bs, shuffle=True)
    
    num_of_first_train = online_x_train.shape[0]

    model = AE(input_dim).to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.001)

    model.train()
    for epoch in range(epochs):
        print('seed = ', (seed+i), ', first round: epoch = ', epoch)
        for j, data in enumerate(train_loader, 0):
            inputs, labels = data
            inputs = inputs.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()

            features, recon_vec = model(inputs)
            loss = criterion(features, labels) + criterion(recon_vec, labels)

            loss.backward()
            optimizer.step()

    x_train = x_train.to(device)
    x_test = x_test.to(device)
    online_x_train, online_y_train = online_x_train.to(device), online_y_train.to(device)

    x_train_this_epoch = online_x_train.clone()
    x_test_left_epoch = online_x_test.clone().to(device)
    y_train_this_epoch = online_y_train.clone()
    y_test_left_epoch = online_y_test.clone()

    ####################### ONLINE TRAINING #######################
    count = 0
    y_train_detection = y_train_this_epoch
    while len(x_test_left_epoch) > 0:
        print('seed = ', (seed+i), ', i = ', count)
        count += 1
        
        if len(x_test_left_epoch) < sample_interval:
            x_test_this_epoch = x_test_left_epoch.clone()
            x_test_left_epoch.resize_(0)
        else:
            x_test_this_epoch = x_test_left_epoch[:sample_interval].clone()
            x_test_left_epoch = x_test_left_epoch[sample_interval:]

        test_features = F.normalize(model(x_test_this_epoch)[0], p=2, dim=1)

        normal_temp = torch.mean(F.normalize(model(online_x_train[(online_y_train == 0).squeeze()])[0], p=2, dim=1), dim=0)
        normal_recon_temp = torch.mean(F.normalize(model(online_x_train[(online_y_train == 0).squeeze()])[1], p=2, dim=1), dim=0)
        predict_label = evaluate(normal_temp, normal_recon_temp, x_train_this_epoch, y_train_detection, x_test_this_epoch, 0, model)

        y_test_pred_this_epoch = predict_label
        y_train_detection = torch.cat((y_train_detection.to(device), torch.tensor(y_test_pred_this_epoch).to(device)))
        num_zero = int(flip_percent * y_test_pred_this_epoch.shape[0])
        zero_indices = np.random.choice(y_test_pred_this_epoch.shape[0], num_zero, replace=False)
        y_test_pred_this_epoch[zero_indices] = 1 - y_test_pred_this_epoch[zero_indices]

        x_train_this_epoch = torch.cat((x_train_this_epoch.to(device), x_test_this_epoch.to(device)))
        y_train_this_epoch_temp = y_train_this_epoch.clone()
        y_train_this_epoch = torch.cat((y_train_this_epoch_temp.to(device), torch.tensor(y_test_pred_this_epoch).to(device)))

        train_ds = TensorDataset(x_train_this_epoch, y_train_this_epoch)
        
        train_loader = torch.utils.data.DataLoader(
            dataset=train_ds, batch_size=bs, shuffle=True)
        model.train()
        for epoch in range(epoch_1):
            print('epoch = ', epoch)
            for j, data in enumerate(train_loader, 0):
                inputs, labels = data
                inputs = inputs.to(device)
                labels = labels.to(device)
                optimizer.zero_grad()

                features, recon_vec = model(inputs)
                loss = criterion(features, labels) + criterion(recon_vec, labels)

                loss.backward()
                optimizer.step()

    ################### EVALUATION FINALE ###################
    print("\n" + "=" * 60)
    print(f"RESULTATS - Round {i+1}")
    print("=" * 60)
    
    normal_temp = torch.mean(F.normalize(model(online_x_train[(online_y_train == 0).squeeze()])[0], p=2, dim=1), dim=0)
    normal_recon_temp = torch.mean(F.normalize(model(online_x_train[(online_y_train == 0).squeeze()])[1], p=2, dim=1), dim=0)

    res_en, res_de, res_final = evaluate(normal_temp, normal_recon_temp, x_train_this_epoch, y_train_detection, x_test, y_test, model)

# =============================================================================
# SAUVEGARDER LES ANOMALIES DETECTEES (NetMob uniquement)
# =============================================================================

if dataset == 'netmob' and test_metadata is not None:
    print("\n" + "=" * 60)
    print("SAUVEGARDE DES RESULTATS")
    print("=" * 60)
    
    # Obtenir les predictions finales
    normal_temp = torch.mean(F.normalize(model(online_x_train[(online_y_train == 0).squeeze()])[0], p=2, dim=1), dim=0)
    normal_recon_temp = torch.mean(F.normalize(model(online_x_train[(online_y_train == 0).squeeze()])[1], p=2, dim=1), dim=0)
    
    # Predire sur le test set (y_test=0 pour obtenir seulement les predictions)
    y_pred_final = evaluate(normal_temp, normal_recon_temp, x_train_this_epoch, y_train_detection, x_test, 0, model)
    
    # Creer le DataFrame des resultats
    results_df = test_metadata.copy()
    results_df['label_reel'] = y_test.cpu().numpy()
    results_df['label_predit'] = y_pred_final.numpy()
    
    # Sauvegarder toutes les predictions
    output_all = args.output_path.replace('.csv', '_all.csv')
    results_df.to_csv(output_all, index=False)
    print(f"[SAVE] Toutes les predictions: {output_all}")
    print(f"       -> {len(results_df)} lignes")
    
    # Sauvegarder seulement les anomalies detectees
    anomalies_df = results_df[results_df['label_predit'] == 1]
    anomalies_df.to_csv(args.output_path, index=False)
    print(f"[SAVE] Anomalies detectees: {args.output_path}")
    print(f"       -> {len(anomalies_df)} anomalies detectees")
    
    # Stats supplementaires
    vrais_positifs = len(results_df[(results_df['label_reel'] == 1) & (results_df['label_predit'] == 1)])
    faux_positifs = len(results_df[(results_df['label_reel'] == 0) & (results_df['label_predit'] == 1)])
    print(f"\n[STATS]")
    print(f"       Vrais positifs (vraies anomalies detectees): {vrais_positifs}")
    print(f"       Faux positifs (fausses alertes): {faux_positifs}")

print("\n" + "=" * 60)
print("TERMINE")
print("=" * 60)
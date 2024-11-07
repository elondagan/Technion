import pickle
import time

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split, RandomSampler
import torch.nn.functional as F
from collections import Counter
import matplotlib.pyplot as plt
from tqdm import tqdm



class ListsDataset(Dataset):

    def __init__(self, raiser_position_, caller_position_, checked_to_, hands_,
                 hands_strength_, flops_strength_, hands_potential_, flops_potential_, cards_order_,
                 treatment_):

        self.raiser_position_ = raiser_position_
        self.caller_position_ = caller_position_
        self.checked_to_ = checked_to_
        self.hands_ = hands_
        self.hands_strength_ = hands_strength_
        self.flops_strength_ = flops_strength_
        self.hands_potential_ = hands_potential_
        self.flops_potential_ = flops_potential_
        self.cards_order_ = cards_order_
        self.treatment_ = treatment_

    def __len__(self):
        return len(self.hands_)

    def __getitem__(self, idx):

        x = [self.raiser_position_[idx], self.caller_position_[idx], self.checked_to_[idx], self.hands_[idx],
         self.hands_strength_[idx], self.flops_strength_[idx], self.hands_potential_[idx], self.flops_potential_[idx],
             self.cards_order_[idx]]
        y = self.treatment_[idx]

        return x, y


class TreatmentPrediction(nn.Module):

    def __init__(self):
        super().__init__()
        self.raiser_pos_embedding = nn.Embedding(6, 1)
        self.caller_pos_embedding = nn.Embedding(6, 1)
        self.hand_embedding = nn.Embedding(196, 3)
        self.hand_strength_embedding = nn.Embedding(10, 2)
        self.flop_strength_embedding = nn.Embedding(4, 2)
        self.hand_potential_embedding = nn.Embedding(16, 2)
        self.flop_potential_embedding = nn.Embedding(4, 2)
        self.order_embedding = nn.Embedding(10, 2)

        self.fc1 = nn.Linear(16, 9)
        self.dropout = nn.Dropout(0.2)
        self.fc2 = nn.Linear(9, 3)  ###

    def forward(self, x):
        raiser_pos, caller_pos, checked_to, hand, hands_strength, flops_strength, hand_pot, flop_pot, cards_ord = x

        raiser_pos_embedded = self.raiser_pos_embedding(raiser_pos)
        caller_pos_embedded = self.raiser_pos_embedding(caller_pos)
        hand_embedded = self.hand_embedding(hand)
        hands_strength_embedded = self.hand_strength_embedding(hands_strength)
        flops_strength_embedded = self.flop_strength_embedding(flops_strength)
        hand_pot_embedded = self.hand_potential_embedding(hand_pot)
        flop_pot_embedded = self.hand_potential_embedding(flop_pot)
        cards_ord_embedded = self.order_embedding(cards_ord)

        checked_to = checked_to.unsqueeze(-1)

        final_x = torch.cat((checked_to, raiser_pos_embedded, caller_pos_embedded,
                             hand_embedded, hands_strength_embedded, flops_strength_embedded, hand_pot_embedded,
                             flop_pot_embedded, cards_ord_embedded), dim=-1)

        final_x = final_x.float()

        out = torch.relu(self.fc1(final_x))
        out = self.dropout(out)
        out = self.fc2(out)
        return out

    def train_model(self, label_balance, train_loader, test_loader, epochs):
        print("Start Training . . .")
        labels_weight = sum(label_balance) / label_balance
        print("labels balance: ", [v.item() / sum(label_balance) for v in label_balance])
        # criterion = nn.CrossEntropyLoss(reduction='sum', weight=labels_weight)
        criterion = nn.CrossEntropyLoss(reduction='sum')
        optimizer = torch.optim.Adam(self.parameters(), lr=0.001)

        tot_loss = []
        test_results = {'loss': [], 'acc': []}
        for epoch in range(epochs):
            epoch_loss = 0.0
            epoch_count = 0

            self.train()
            for batch in train_loader:
                cur_x, cur_y = batch
                output = self(cur_x)
                loss = criterion(output, cur_y)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
                epoch_count += len(cur_y)

            epoch_loss_val = epoch_loss / epoch_count
            tot_loss.append(epoch_loss_val)
            if epoch % 10 == 0:
                print(f'Epoch {epoch + 1}/{num_epochs}, Loss: {epoch_loss_val}')

            if test_loader is not None:
                avg_loss, acc = self.evaluate_model(labels_weight, test_loader, epoch)
                test_results['loss'].append(avg_loss)
                test_results['acc'].append(acc)

        plt.plot(tot_loss, label='train')
        if test_loader is not None:
            plt.plot(test_results['loss'], label='test')

        print("---train------")
        train_acc = self.evaluate_model(None, train_loader, 0)

        plt.legend()
        plt.title("Action Probability Estimation Model")
        plt.xlabel("epoch")
        plt.ylabel("bce loss")
        plt.show()
        print(f"best test acc = {max(test_results['acc'])}")
        print(f"model accuracy on train = {train_acc[1]}")

    def evaluate_model(self, labels_weight, test_loader, c_epoch):
        self.eval()
        # criterion = nn.CrossEntropyLoss(reduction='sum', weight=labels_weight)
        criterion = nn.CrossEntropyLoss(reduction='sum')

        tot_loss = 0.0
        correct_predictions = 0
        total_samples = 0

        with torch.no_grad():
            for batch in test_loader:

                cur_x, cur_y = batch

                output = self(cur_x)

                loss = criterion(output, cur_y)
                predictions = torch.argmax(output, dim=1)
                acc = (predictions == cur_y).float().mean()

                tot_loss += loss.item()
                correct_predictions += acc.item() * len(cur_y)
                total_samples += len(cur_y)

        avg_loss = tot_loss / total_samples
        accuracy = correct_predictions / total_samples
        if c_epoch % 10 == 0:
            print(f'Average Cross-Entropy Loss: {avg_loss}')
            print(f'Accuracy: {accuracy * 100:.2f}%')
        return avg_loss, accuracy


if __name__ == '__main__':

    with open('data/lists_data.pkl', 'rb') as file:
        all_lists = pickle.load(file)

    # op 1
    treatments = [0 if v < 0.48 else (1 if v < 0.52 else 2) for v in all_lists[0]]
    # # op 2
    # treatments = []
    # for v in all_lists[0]:
    #     if v < 0.45:
    #         treatments.append(0)
    #     elif v < 0.55:
    #         treatments.append(1)
    #     elif v < 0.7:
    #         treatments.append(2)
    #     else:
    #         treatments.append(3)
    # op 3
    # treatments = [int(v*10 - 3) for v in all_lists[0]]
    # treatments = [v if v >= 0 else 0 for v in treatments]


    outcomes = all_lists[1]
    raiser_position = all_lists[2]
    caller_position = all_lists[3]
    checked_to = all_lists[8]
    hands, hands_strength, flops_strength, hands_potential, flops_potential = all_lists[9:-2]
    cards_order = all_lists[-2]

    dataset = ListsDataset(raiser_position, caller_position, checked_to, hands,
                           hands_strength, flops_strength, hands_potential, flops_potential, cards_order,
                           treatments)
    dataset_size = len(dataset)


    final_res = []

    for _ in tqdm(range(1)):  # 1000

        num_epochs = 10
        batch_size = 10

        sampler = RandomSampler(dataset, replacement=True, num_samples=dataset_size)
        dataloader = DataLoader(dataset, sampler=sampler, batch_size=batch_size)

        model = TreatmentPrediction()
        model.train_model(None, dataloader, None, epochs=num_epochs)

        torch.save(model.state_dict(), 'treatment_prediction_model.pth')

        probabilities = []
        reals = []
        for i in range(dataset_size):
            x, t = dataset[i]
            x = [torch.tensor(f) for f in x]
            with torch.no_grad():
                logits = model(x)
                probs = torch.softmax(logits, dim=0).tolist()
                probabilities.append(probs)
                reals.append(t)
        # __________

        ws = []
        for i in range(dataset_size):
            wi = 1 / probabilities[i][reals[i]]
            ws.append(wi)
        # ______

        pr_y_t = {'T=0': {'Outcome=0': 0, 'Outcome=1': 0, 'Outcome=2': 0},
                  'T=1': {'Outcome=0': 0, 'Outcome=1': 0, 'Outcome=2': 0},
                  'T=2': {'Outcome=0': 0, 'Outcome=1': 0, 'Outcome=2': 0}}

        for t in range(3):

            cur_treatment_indices = [i for i in range(dataset_size) if treatments[i] == t]
            den = sum([ws[i] for i in cur_treatment_indices])

            for y in range(3):
                cur_outcome_indices = [i for i in range(dataset_size) if outcomes[i] == y]
                rel_indices = [i for i in range(dataset_size) if i in cur_outcome_indices and i in cur_treatment_indices]
                num = sum([ws[i] for i in rel_indices])
                pr_y_t[f"T={t}"][f"Outcome={y}"] = num / den

        final_res.append(pr_y_t)

    with open("final_results.pkl", 'wb') as file:
        pickle.dump(final_res, file)

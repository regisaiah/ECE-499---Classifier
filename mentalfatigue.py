# |MODULES|--------------------------------------------------------------------
import sys
import os.path
MODULE_PATH = os.path.dirname(__file__)
import pandas as pd
import pickle as pk


def assess(x):
    clf = pk.load(open(os.path.join(MODULE_PATH,'finalized_model.sav'), 'rb'))
    mean = pk.load(open(os.path.join(MODULE_PATH,'mean.sav'), 'rb'))
    var = pk.load(open(os.path.join(MODULE_PATH,'var.sav'), 'rb'))
    x = (x - mean)/var
    x = x.to_numpy().reshape(1, -1)
    return clf.predict(x)[0]


if __name__ == "__main__":
    test = pd.read_csv('trainlist.csv')
    y = test.loc[:, "Class"].to_numpy()
    test = test.iloc[:, 1:-2]
    for i in range(test.shape[0]):
        #for j, val in enumerate(test.iloc[i].to_list()):
        #    print("{}\t{}\n".format(j, val))
        print(assess(test.iloc[i]))

    # clf = pk.load(open('finalized_model.sav', 'rb'))
    # mean = pk.load(open('mean.sav', 'rb'))
    # print(mean)
    # var = pk.load(open('var.sav', 'rb'))
    # print(var)
    # test = (test - mean)/var
    # test = test.to_numpy()

    # predict = clf.score(test, y)
    # print(predict)


        #print(assess(sample.reshape(1, -1)))
    #train = pd.read_csv('testlist.csv')
    #mean = train.iloc[:, 1:-2].mean(axis=0).to_list()
    #var = train.iloc[:, 1:-2].std(axis=0).to_list()
    #pk.dump(mean, open('mean.sav', 'wb'))
    #pk.dump(var, open('var.sav', 'wb'))
    #print(test)
    #print(mean)
    #print(var)

    sys.exit(0)

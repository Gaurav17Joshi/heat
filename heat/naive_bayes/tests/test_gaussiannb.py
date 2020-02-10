import os
import unittest

import heat as ht
from heat.core.tests.test_suites.basic_test import BasicTest

if os.environ.get("DEVICE") == "gpu" and ht.torch.cuda.is_available():
    ht.use_device("gpu")
    ht.torch.cuda.set_device(ht.torch.device(ht.get_device().torch_device))
else:
    ht.use_device("cpu")
device = ht.get_device().torch_device
ht_device = None
if os.environ.get("DEVICE") == "lgpu" and ht.torch.cuda.is_available():
    device = ht.gpu.torch_device
    ht_device = ht.gpu
    ht.torch.cuda.set_device(device)


class TestGaussianNB(BasicTest):
    def test_fit_iris(self):
        X_train = ht.load("heat/datasets/data/iris_X_train.csv", sep=";")
        X_test = ht.load("heat/datasets/data/iris_X_test.csv", sep=";")
        y_train = ht.load("heat/datasets/data/iris_y_train.csv", sep=";", dtype=ht.int32).squeeze()
        y_test = ht.load("heat/datasets/data/iris_y_test.csv", sep=";", dtype=ht.int32).squeeze()

        # test ht.GaussianNB
        from heat.naive_bayes import GaussianNB

        gnb_heat = GaussianNB()

        # test ht.GaussianNB locally
        y_pred_local = gnb_heat.fit(X_train, y_train).predict(X_test)
        self.assertIsInstance(y_pred_local, ht.DNDarray)
        self.assertEqual((y_pred_local != y_test).sum(), ht.array(4))

        # #test ht.GaussianNB, data and labels distributed along split axis 0
        size = ht.MPI_WORLD.size
        if size in range(7):
            X_train_split = ht.resplit(X_train, axis=0)
            X_test_split = ht.resplit(X_test, axis=0)
            y_train_split = ht.resplit(y_train, axis=0)
            y_test_split = ht.resplit(y_test, axis=0)
            y_pred_split = gnb_heat.fit(X_train_split, y_train_split).predict(X_test_split)
            self.assert_array_equal(y_pred_split, y_pred_local.numpy())
            self.assertEqual((y_pred_split != y_test_split).sum(), ht.array(4))

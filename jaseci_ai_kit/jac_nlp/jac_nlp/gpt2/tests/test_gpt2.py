from jaseci.utils.test_core import CoreTest, jac_testcase
from jaseci.jsorc.live_actions import load_module_actions, unload_module
import pytest
import shutil
from pathlib import Path


class GPT2Tests(CoreTest):
    fixture_src = __file__

    @classmethod
    def setUpClass(cls):
        super(GPT2Tests, cls).setUpClass()
        ret = load_module_actions("jac_nlp.gpt2")
        assert ret is True

    @pytest.mark.order(1)
    @jac_testcase("gpt2.jac", "test_generate")
    def test_generate(self, ret):
        self.assertEqual(len(ret["report"][0][0]), 5)

    @pytest.mark.order(2)
    @jac_testcase("gpt2.jac", "test_get_embeddings")
    def test_get_embeddings(self, ret):
        self.assertEqual(len(ret["report"][0]), 2)
        self.assertEqual(len(ret["report"][0][0][0]), 768)

    # TODO: optimize the test for gpt2 train
    # @pytest.mark.order(3)
    # @jac_testcase("gpt2.jac", "test_train")
    # def test_train(self, ret):
    #     self.assertEqual(ret["success"], True)

    # @pytest.mark.order(4)
    # @jac_testcase("gpt2.jac", "test_generate_trained")
    # def test_generate_trained(self, ret):
    #     self.assertEqual(len(ret["report"][0][0]), 5)

    @classmethod
    def tearDownClass(cls):
        super(GPT2Tests, cls).tearDownClass()
        ret = unload_module("jac_nlp.gpt2.gpt2")
        assert ret is True
        shutil.rmtree(Path(Path.home(), ".jaseci/models/jac_nlp/gpt2"))

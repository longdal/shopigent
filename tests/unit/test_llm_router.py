"""LLMRouter 단위 테스트 — 태스크별 모델 라우팅."""

from unittest.mock import patch

from shopigent.llm.router import LLMRouter, LLMTaskType


class TestLLMRouter:
    """LLMRouter 라우팅 로직 검증."""

    def setup_method(self):
        self.router = LLMRouter()


    @patch.object(LLMRouter, "_is_ollama_available", return_value=True)
    def test_product_analyze_uses_ollama_when_available(self, mock_ollama):
        model = self.router.get_model(LLMTaskType.PRODUCT_ANALYZE)
        assert "ollama" in model


    @patch.object(LLMRouter, "_is_ollama_available", return_value=False)
    def test_product_analyze_fallback_when_ollama_unavailable(self, mock_ollama):
        model = self.router.get_model(LLMTaskType.PRODUCT_ANALYZE)
        assert "ollama" not in model
        assert "gemini" in model


    @patch.object(LLMRouter, "_is_ollama_available", return_value=True)
    def test_report_generate_uses_cloud_model(self, mock_ollama):
        model = self.router.get_model(LLMTaskType.REPORT_GENERATE)
        assert "ollama" not in model


    @patch.object(LLMRouter, "_is_ollama_available", return_value=True)
    def test_all_task_types_have_routing(self, mock_ollama):
        for task_type in LLMTaskType:
            model = self.router.get_model(task_type)
            assert model, f"{task_type.name}에 라우팅이 없습니다"


    @patch.object(LLMRouter, "_is_ollama_available", return_value=True)
    def test_get_model_returns_string(self, mock_ollama):
        for task_type in LLMTaskType:
            model = self.router.get_model(task_type)
            assert isinstance(model, str)

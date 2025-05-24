import pystache
import pathlib
from typing import List, Dict, Any

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent # app/

class ChatPromptFactory:
    
    @staticmethod
    def _load_and_render(template_name: str, data: Dict[str, Any]) -> str:
        template_file_path = BASE_DIR / "templates" / "prompts" / template_name
        try:
            with open(template_file_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
            return pystache.render(prompt_template, data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt template not found: {template_file_path}")
        except Exception as e:
            raise Exception(f"Error rendering prompt template {template_name}: {e}")

    @staticmethod
    def rag_decision_prompt(history: List[Dict[str, str]], user_question: str) -> str:
        """
        Generates the prompt for deciding whether RAG is needed.
        history: List of {"role": "user/assistant", "content": "..."}
        """
        data = {"history": history, "user_question": user_question}
        return ChatPromptFactory._load_and_render("rag_decision.mustache", data)

    @staticmethod
    def rag_answer_prompt(history: List[Dict[str, str]], user_question: str, context_chunks: List[Dict[str, Any]]) -> str:
        formatted_context_chunks_for_template = []
        for i, chunk_data in enumerate(context_chunks):
            formatted_context_chunks_for_template.append({
                "index_1": i + 1,
                "text": chunk_data.get("text"),
                "metadata": chunk_data.get("metadata", {})
            })
        data = {
            "history": history,
            "user_question": user_question,
            "context_chunks": formatted_context_chunks_for_template
        }
        return ChatPromptFactory._load_and_render("rag_answer.mustache", data)
    
    @staticmethod
    def normal_answer_prompt(history: List[Dict[str, str]], user_question: str) -> str:
        """
        Generates the prompt for answering without RAG.
        """
        data = {"history": history, "user_question": user_question}
        return ChatPromptFactory._load_and_render("normal_answer.mustache", data)
import openai
from typing import Optional, Dict, Any
import os
import logging
from datetime import datetime

# Thiết lập logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

class CodeAssistant:
    def __init__(self):
        """
        Khởi tạo Code Assistant với OpenAI API key
        """
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.error("OpenAI API key not found in environment variables")
            raise ValueError("OpenAI API key not found")
            
        openai.api_key = self.api_key
        logger.debug("CodeAssistant initialized successfully")
        
        # Cấu hình mặc định
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 2000
        self.temperature = 0.7
        
    def create_prompt(self, query: str, code_context: str, language: str) -> str:
        """
        Tạo prompt cho OpenAI API
        """
        prompt_parts = [
            f"Language: {language}",
            f"Code Context: {code_context}" if code_context else "",
            f"Question: {query}",
            "Please provide a clear explanation and code example."
        ]
        return "\n".join(filter(None, prompt_parts))

    def format_response(self, ai_response: str) -> str:
        """
        Format response từ AI để dễ đọc hơn
        """
        # Thêm markdown formatting nếu cần
        return ai_response.strip()

    def process_request(
        self, 
        query: str, 
        code_context: Optional[str] = '', 
        language: str = 'python'
    ) -> Dict[str, Any]:
        """
        Xử lý yêu cầu và trả về response từ OpenAI
        """
        try:
            # Log request
            logger.debug(f"Processing request - Query: {query[:100]}...")
            
            # Validate inputs
            if not query:
                return {
                    'success': False,
                    'error': 'Query is required'
                }
                
            # Tạo prompt
            prompt = self.create_prompt(query, code_context, language)
            
            # Gọi OpenAI API
            start_time = datetime.now()
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert programming assistant. "
                            "Provide clear, concise, and practical answers "
                            "with code examples when appropriate."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                n=1,
                stop=None
            )
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"OpenAI API response time: {response_time:.2f} seconds")
            
            # Extract and format response
            ai_response = response.choices[0].message.content
            formatted_response = self.format_response(ai_response)
            
            # Log success
            logger.debug(
                f"Request processed successfully - "
                f"Tokens used: {response.usage.total_tokens}"
            )
            
            return {
                'success': True,
                'response': formatted_response,
                'tokens_used': response.usage.total_tokens,
                'response_time': response_time,
                'model': self.model
            }
            
        except openai.error.AuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid OpenAI API key'
            }
            
        except openai.error.RateLimitError as e:
            logger.error(f"Rate limit error: {str(e)}")
            return {
                'success': False,
                'error': 'OpenAI API rate limit exceeded'
            }
            
        except openai.error.InvalidRequestError as e:
            logger.error(f"Invalid request error: {str(e)}")
            return {
                'success': False,
                'error': f'Invalid request: {str(e)}'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'success': False,
                'error': f'An unexpected error occurred: {str(e)}'
            }

    def validate_language(self, language: str) -> bool:
        """
        Kiểm tra ngôn ngữ lập trình có được hỗ trợ không
        """
        supported_languages = [
            'python', 'javascript', 'java', 'c++', 'c#',
            'php', 'ruby', 'swift', 'go', 'rust'
        ]
        return language.lower() in supported_languages

    def get_example_response(self, language: str) -> Dict[str, Any]:
        """
        Trả về ví dụ mẫu cho testing
        """
        examples = {
            'python': {
                'query': 'How to sort a list?',
                'response': '''
                In Python, you can sort a list using the sort() method or sorted() function:

                ```python
                # Using sort() method (modifies original list)
                my_list = [3, 1, 4, 1, 5, 9]
                my_list.sort()
                print(my_list)  # Output: [1, 1, 3, 4, 5, 9]

                # Using sorted() function (returns new list)
                my_list = [3, 1, 4, 1, 5, 9]
                sorted_list = sorted(my_list)
                print(sorted_list)  # Output: [1, 1, 3, 4, 5, 9]
                ```
                '''
            }
        }
        return examples.get(language, {
            'query': 'Example not available for this language',
            'response': 'No example available'
        })
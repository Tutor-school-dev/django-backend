from django.core.management.base import BaseCommand
from django.conf import settings
from config.logger import get_logger
import os

logger = get_logger(__name__)


class Command(BaseCommand):
    help = 'Diagnose AI configuration and connectivity (OpenAI and Gemini)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 AI Configuration Diagnostics'))
        self.stdout.write('='*50)
        
        # Check which AI provider is selected
        ai_provider = getattr(settings, 'GEN_AI', 'openai').lower()
        self.stdout.write(f'🤖 Selected AI Provider: {ai_provider.upper()}')
        self.stdout.write('')
        
        if ai_provider == 'gemini':
            success = self._diagnose_gemini()
        else:
            success = self._diagnose_openai()
        
        if not success:
            return
        
        # Check environment file
        self._check_env_file()
        
        # Test AI service initialization
        self._test_ai_service()
        
        # Show next steps
        self._show_next_steps()
    
    def _diagnose_openai(self):
        """Diagnose OpenAI configuration"""
        self.stdout.write('🔧 OpenAI Diagnostics:')
        
        # Check OpenAI package installation
        try:
            import openai
            self.stdout.write(self.style.SUCCESS('✅ OpenAI package is installed'))
            self.stdout.write(f'   Version: {openai.__version__}')
        except ImportError as e:
            self.stdout.write(self.style.ERROR('❌ OpenAI package is NOT installed'))
            self.stdout.write(f'   Error: {e}')
            self.stdout.write('   Fix: pip install openai==1.58.1')
            return False
        
        # Check API key configuration
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if api_key:
            self.stdout.write(self.style.SUCCESS('✅ OPENAI_API_KEY is configured'))
            self.stdout.write(f'   Length: {len(api_key)} characters')
            self.stdout.write(f'   Starts with: {api_key[:10]}...')
        else:
            self.stdout.write(self.style.ERROR('❌ OPENAI_API_KEY is NOT configured'))
            self.stdout.write('   Check your .env file or environment variables')
            return False
        
        # Test OpenAI client initialization
        try:
            client = openai.OpenAI(api_key=api_key)
            self.stdout.write(self.style.SUCCESS('✅ OpenAI client initialized successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR('❌ OpenAI client initialization failed'))
            self.stdout.write(f'   Error: {e}')
            return False
        
        # Test API connectivity (optional)
        test_api = input('\\n🤔 Test OpenAI API connectivity? This will make a small API call (~$0.001): (y/N) ')
        if test_api.lower() == 'y':
            try:
                self.stdout.write('🔄 Testing OpenAI API connectivity...')
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a test assistant."},
                        {"role": "user", "content": "Say 'API test successful'"}
                    ],
                    max_tokens=10
                )
                result = response.choices[0].message.content.strip()
                self.stdout.write(self.style.SUCCESS('✅ OpenAI API connectivity test successful'))
                self.stdout.write(f'   Response: {result}')
            except Exception as e:
                self.stdout.write(self.style.ERROR('❌ OpenAI API connectivity test failed'))
                self.stdout.write(f'   Error: {e}')
                return False
        
        # Show OpenAI settings
        self.stdout.write('\\n📋 OpenAI Settings:')
        self.stdout.write(f'   Model: {getattr(settings, "OPENAI_MODEL", "Not set")}')
        self.stdout.write(f'   Max Tokens: {getattr(settings, "OPENAI_MAX_TOKENS", "Not set")}')
        self.stdout.write(f'   Timeout: {getattr(settings, "OPENAI_TIMEOUT", "Not set")}s')
        
        return True
    
    def _diagnose_gemini(self):
        """Diagnose Gemini configuration"""
        self.stdout.write('🔧 Gemini Diagnostics:')
        
        # Check Gemini package installation
        try:
            import google.generativeai as genai
            self.stdout.write(self.style.SUCCESS('✅ Google Generative AI package is installed'))
            self.stdout.write(f'   Package: google-generativeai')
        except ImportError as e:
            self.stdout.write(self.style.ERROR('❌ Google Generative AI package is NOT installed'))
            self.stdout.write(f'   Error: {e}')
            self.stdout.write('   Fix: pip install google-generativeai==0.8.3')
            return False
        
        # Check API key configuration
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if api_key:
            self.stdout.write(self.style.SUCCESS('✅ GEMINI_API_KEY is configured'))
            self.stdout.write(f'   Length: {len(api_key)} characters')
            self.stdout.write(f'   Starts with: {api_key[:10]}...')
        else:
            self.stdout.write(self.style.ERROR('❌ GEMINI_API_KEY is NOT configured'))
            self.stdout.write('   Check your .env file or environment variables')
            return False
        
        # Test Gemini client initialization
        try:
            genai.configure(api_key=api_key)
            client = genai.GenerativeModel('gemini-2.5-sflash-lite')
            self.stdout.write(self.style.SUCCESS('✅ Gemini client initialized successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR('❌ Gemini client initialization failed'))
            self.stdout.write(f'   Error: {e}')
            return False
        
        # Test API connectivity (optional)
        test_api = input('\\n🤔 Test Gemini API connectivity? This will make a small API call (~$0.001): (y/N) ')
        if test_api.lower() == 'y':
            try:
                self.stdout.write('🔄 Testing Gemini API connectivity...')
                response = client.generate_content(
                    "Say 'API test successful'",
                    generation_config={'max_output_tokens': 10, 'temperature': 0.1}
                )
                result = response.text.strip()
                self.stdout.write(self.style.SUCCESS('✅ Gemini API connectivity test successful'))
                self.stdout.write(f'   Response: {result}')
            except Exception as e:
                self.stdout.write(self.style.ERROR('❌ Gemini API connectivity test failed'))
                self.stdout.write(f'   Error: {e}')
                return False
        
        # Show Gemini settings
        self.stdout.write('\\n📋 Gemini Settings:')
        self.stdout.write(f'   Model: {getattr(settings, "GEMINI_MODEL", "Not set")}')
        self.stdout.write(f'   Max Tokens: {getattr(settings, "GEMINI_MAX_TOKENS", "Not set")}')
        self.stdout.write(f'   Timeout: {getattr(settings, "GEMINI_TIMEOUT", "Not set")}s')
        
        return True
    
    def _check_env_file(self):
        """Check environment file"""
        env_file_path = os.path.join(settings.BASE_DIR, '.env')
        if os.path.exists(env_file_path):
            self.stdout.write(self.style.SUCCESS('\\n✅ .env file exists'))
            with open(env_file_path, 'r') as f:
                env_content = f.read()
                
                ai_provider = getattr(settings, 'GEN_AI', 'openai').lower()
                if ai_provider == 'gemini':
                    if 'GEMINI_API_KEY' in env_content:
                        self.stdout.write('   ✅ GEMINI_API_KEY found in .env')
                    else:
                        self.stdout.write('   ⚠️ GEMINI_API_KEY not found in .env')
                else:
                    if 'OPENAI_API_KEY' in env_content:
                        self.stdout.write('   ✅ OPENAI_API_KEY found in .env')
                    else:
                        self.stdout.write('   ⚠️ OPENAI_API_KEY not found in .env')
                
                if 'GEN_AI' in env_content:
                    self.stdout.write('   ✅ GEN_AI provider setting found')
                else:
                    self.stdout.write('   ⚠️ GEN_AI provider setting not found (defaults to openai)')
        else:
            self.stdout.write(self.style.WARNING('\\n⚠️ .env file not found'))
    
    def _test_ai_service(self):
        """Test AI service initialization"""
        try:
            from learner.services.ai_service import AIMatchingService
            ai_service = AIMatchingService()
            self.stdout.write(self.style.SUCCESS('\\n✅ AI Matching Service initialized successfully'))
            self.stdout.write(f'   Using provider: {ai_service.ai_provider}')
            self.stdout.write(f'   Model: {ai_service.model}')
        except Exception as e:
            self.stdout.write(self.style.ERROR('\\n❌ AI Matching Service initialization failed'))
            self.stdout.write(f'   Error: {e}')
            return False
        return True
    
    def _show_next_steps(self):
        """Show next steps"""
        self.stdout.write('\\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('🎉 All AI diagnostics passed!'))
        self.stdout.write('You can now test the matching API.')
        
        ai_provider = getattr(settings, 'GEN_AI', 'openai').lower()
        self.stdout.write(f'\\n🔄 To switch AI providers, change GEN_AI in .env:')
        self.stdout.write('   GEN_AI=openai   # for OpenAI GPT models')
        self.stdout.write('   GEN_AI=gemini   # for Google Gemini models')
        
        self.stdout.write('\\n📝 Next steps:')
        self.stdout.write('1. Run: python manage.py create_test_data')
        self.stdout.write('2. Use the JWT token to test the API')
        self.stdout.write('3. Check logs in logs/application-logs.log for detailed info')
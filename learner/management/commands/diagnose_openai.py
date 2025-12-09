from django.core.management.base import BaseCommand
from django.conf import settings
from config.logger import get_logger
import os

logger = get_logger(__name__)


class Command(BaseCommand):
    help = 'Diagnose OpenAI configuration and connectivity'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 OpenAI Configuration Diagnostics'))
        self.stdout.write('='*50)
        
        # Check OpenAI package installation
        try:
            import openai
            self.stdout.write(self.style.SUCCESS('✅ OpenAI package is installed'))
            self.stdout.write(f'   Version: {openai.__version__}')
        except ImportError as e:
            self.stdout.write(self.style.ERROR('❌ OpenAI package is NOT installed'))
            self.stdout.write(f'   Error: {e}')
            self.stdout.write('   Fix: pip install openai==1.58.1')
            return
        
        # Check API key configuration
        api_key = getattr(settings, 'OPENAI_API_KEY', '')
        if api_key:
            self.stdout.write(self.style.SUCCESS('✅ OPENAI_API_KEY is configured'))
            self.stdout.write(f'   Length: {len(api_key)} characters')
            self.stdout.write(f'   Starts with: {api_key[:10]}...')
        else:
            self.stdout.write(self.style.ERROR('❌ OPENAI_API_KEY is NOT configured'))
            self.stdout.write('   Check your .env file or environment variables')
            return
        
        # Check environment file
        env_file_path = os.path.join(settings.BASE_DIR, '.env')
        if os.path.exists(env_file_path):
            self.stdout.write(self.style.SUCCESS('✅ .env file exists'))
            with open(env_file_path, 'r') as f:
                env_content = f.read()
                if 'OPENAI_API_KEY' in env_content:
                    self.stdout.write('   ✅ OPENAI_API_KEY found in .env')
                else:
                    self.stdout.write('   ⚠️ OPENAI_API_KEY not found in .env')
        else:
            self.stdout.write(self.style.WARNING('⚠️ .env file not found'))
        
        # Test OpenAI client initialization
        try:
            client = openai.OpenAI(api_key=api_key)
            self.stdout.write(self.style.SUCCESS('✅ OpenAI client initialized successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR('❌ OpenAI client initialization failed'))
            self.stdout.write(f'   Error: {e}')
            return
        
        # Test API connectivity (optional - costs money)
        test_api = input('\n🤔 Test API connectivity? This will make a small API call (~$0.001): (y/N) ')
        if test_api.lower() == 'y':
            try:
                self.stdout.write('🔄 Testing API connectivity...')
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a test assistant."},
                        {"role": "user", "content": "Say 'API test successful'"}
                    ],
                    max_tokens=10
                )
                result = response.choices[0].message.content.strip()
                self.stdout.write(self.style.SUCCESS('✅ API connectivity test successful'))
                self.stdout.write(f'   Response: {result}')
            except Exception as e:
                self.stdout.write(self.style.ERROR('❌ API connectivity test failed'))
                self.stdout.write(f'   Error: {e}')
                return
        
        # Check other OpenAI settings
        self.stdout.write('\n📋 OpenAI Settings:')
        self.stdout.write(f'   Model: {getattr(settings, "OPENAI_MODEL", "Not set")}')
        self.stdout.write(f'   Max Tokens: {getattr(settings, "OPENAI_MAX_TOKENS", "Not set")}')
        self.stdout.write(f'   Timeout: {getattr(settings, "OPENAI_TIMEOUT", "Not set")}s')
        
        # Test AI service initialization
        try:
            from learner.services.ai_service import AIMatchingService
            ai_service = AIMatchingService()
            self.stdout.write(self.style.SUCCESS('✅ AI Matching Service initialized successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR('❌ AI Matching Service initialization failed'))
            self.stdout.write(f'   Error: {e}')
            return
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('🎉 All OpenAI diagnostics passed!'))
        self.stdout.write('You can now test the matching API.')
        
        # Show next steps
        self.stdout.write('\n📝 Next steps:')
        self.stdout.write('1. Run: python manage.py create_test_data')
        self.stdout.write('2. Use the JWT token to test the API')
        self.stdout.write('3. Check logs in logs/application-logs.log for detailed info')
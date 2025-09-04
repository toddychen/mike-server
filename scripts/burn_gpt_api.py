#!/usr/bin/env python3
"""
Script to burn GPT API usage by sending long texts for summarization
This helps unlock the next tier by consuming the $5 credit
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import time
import logging

# Load environment variables from .env file
load_dotenv()

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from services.fake_summarizer import NewsSummarizer
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def read_long_text_from_file(file_path: str) -> str:
    """Read long text from a file in the data folder"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        word_count = len(content.split())
        logging.info(f"✅ Successfully read text from {file_path}")
        logging.info(f"📊 Text stats: {len(content)} characters, {word_count} words")
        
        return content
        
    except FileNotFoundError:
        logging.error(f"❌ File not found: {file_path}")
        return None
    except Exception as e:
        logging.error(f"❌ Error reading file: {e}")
        return None

def burn_gpt_api_usage(text: str, summarizer: NewsSummarizer, max_iterations: int = 1):
    """Burn GPT API usage by repeatedly summarizing the same text"""
    
    logging.info(f"🔥 Starting GPT API usage burn...")
    logging.info(f"📝 Text length: {len(text)} characters, {len(text.split())} words")
    logging.info(f"🔄 Max iterations: {max_iterations}")
    
    total_tokens_used = 0
    successful_summaries = 0
    failed_summaries = 0
    
    for i in range(max_iterations):
        try:
            logging.info(f"\n{'='*50}")
            logging.info(f"🔄 Iteration {i+1}/{max_iterations}")
            logging.info(f"{'='*50}")
            
            # Send text for summarization
            result = summarizer.summarize(text)
            
            if result['success']:
                successful_summaries += 1
                tokens_used = result.get('tokens_used', {})
                input_tokens = tokens_used.get('input', 0)
                output_tokens = tokens_used.get('output', 0)
                total_tokens = tokens_used.get('total', 0)
                
                total_tokens_used += total_tokens
                
                logging.info(f"✅ Summary successful!")
                logging.info(f"📊 Summary: {result.get('summary_word_count', 0)} words")
                logging.info(f"💹 Tokens used: input={input_tokens}, output={output_tokens}, total={total_tokens}")
                logging.info(f"💰 Cumulative tokens: {total_tokens_used}")
                
            else:
                failed_summaries += 1
                error_msg = result.get('error', 'Unknown error')
                logging.warning(f"❌ Summary failed: {error_msg}")
                
                # Check if it's a rate limit error
                if 'rate limit' in error_msg.lower() or '429' in error_msg:
                    logging.warning(f"⏳ Rate limit hit, waiting 60 seconds before next attempt...")
                    time.sleep(60)
                    continue
            
            # Add delay between requests to avoid rate limiting
            if i < max_iterations - 1:  # Don't delay after the last iteration
                delay = 62 
                logging.info(f"⏳ Waiting {delay} seconds before next request...")
                time.sleep(delay)
                
        except Exception as e:
            failed_summaries += 1
            logging.error(f"❌ Exception during iteration {i+1}: {e}")
            continue
    
    # Final summary
    logging.info(f"\n{'='*60}")
    logging.info(f"🎉 GPT API usage burn completed!")
    logging.info(f"{'='*60}")
    logging.info(f"📊 Results:")
    logging.info(f"   ✅ Successful summaries: {successful_summaries}")
    logging.info(f"   ❌ Failed summaries: {failed_summaries}")
    logging.info(f"   💰 Total tokens used: {total_tokens_used}")
    logging.info(f"   💵 Estimated cost: ${total_tokens_used / 1000000 * 0.80:.4f} (input) + ${total_tokens_used / 1000000 * 3.20:.4f} (output)")
    
    return {
        'successful_summaries': successful_summaries,
        'failed_summaries': failed_summaries,
        'total_tokens_used': total_tokens_used
    }

def main():
    """Main function"""
    
    print("🔥 GPT API Usage Burn Script")
    print("=" * 50)
    
    # Check if OpenAI API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set OPENAI_API_KEY in your .env file")
        sys.exit(1)
    
    try:
        summarizer = NewsSummarizer(model="gpt-5-nano")
        print("✅ NewsSummarizer initialized successfully with gpt-5-nano model")
    except Exception as e:
        print(f"❌ Failed to initialize NewsSummarizer: {e}")
        sys.exit(1)
    
    # Look for text files in data folder
    data_folder = Path(__file__).parent.parent / "data"
    text_files = list(data_folder.glob("*.txt")) + list(data_folder.glob("*.md"))
    
    if not text_files:
        print("❌ No text files found in data folder")
        print("Please add a .txt or .md file to the data folder")
        sys.exit(1)
    
    print(f"\n📁 Found {len(text_files)} text files in data folder:")
    for i, file_path in enumerate(text_files):
        print(f"   {i+1}. {file_path.name}")
    
    # Let user choose file
    if len(text_files) == 1:
        selected_file = text_files[0]
        print(f"\n📖 Using the only available file: {selected_file.name}")
    else:
        try:
            choice = int(input(f"\nSelect file (1-{len(text_files)}): ")) - 1
            if 0 <= choice < len(text_files):
                selected_file = text_files[choice]
            else:
                print("❌ Invalid choice")
                sys.exit(1)
        except ValueError:
            print("❌ Invalid input")
            sys.exit(1)
    
    # Read the selected file
    print(f"\n📖 Reading file: {selected_file.name}")
    text_content = read_long_text_from_file(str(selected_file))
    
    if not text_content:
        print("❌ Failed to read text content")
        sys.exit(1)
    
    # Check if text is long enough
    word_count = len(text_content.split())
    if word_count < 100:
        print(f"⚠️  Warning: Text is only {word_count} words, which may not be optimal for burning API usage")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted")
            sys.exit(0)
    
    # Get number of iterations
    try:
        max_iterations = int(input(f"\nEnter number of iterations (default: 10): ") or "10")
        if max_iterations <= 0:
            print("❌ Number of iterations must be positive")
            sys.exit(1)
    except ValueError:
        print("❌ Invalid input, using default: 10")
        max_iterations = 10
    
    print(f"\n🚀 Starting GPT API usage burn with {max_iterations} iterations...")
    print("Press Ctrl+C to stop early")
    
    try:
        # Start burning API usage
        result = burn_gpt_api_usage(text_content, summarizer, max_iterations)
        
        print(f"\n🎉 Burn completed successfully!")
        print(f"💰 Total tokens used: {result['total_tokens_used']:,}")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Burn stopped by user")
    except Exception as e:
        print(f"\n❌ Error during burn: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

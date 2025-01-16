from transformers import pipeline, T5Tokenizer, T5ForConditionalGeneration
from datetime import datetime, timedelta, timezone
import sentencepiece
import torch
import re
from typing import Dict, Any

class ReminderParser:
    def __init__(self):
        # Load T5 model and tokenizer for text understanding
        self.model_name = "google-t5/t5-small"  # Can use larger models for better accuracy
        self.tokenizer = T5Tokenizer.from_pretrained(self.model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(self.model_name)
        
        # Time extraction pipeline using a general-purpose classifier
        self.time_classifier = pipeline(
            "text-classification",
            model="distilbert-base-uncased",  # Using a more common model
            return_all_scores=True
        )
        
        # Time patterns for regex backup
        self.time_patterns = {
            r'in (\d+) hour': lambda x: timedelta(hours=int(x)),
            r'in (\d+) minute': lambda x: timedelta(minutes=int(x)),
            r'in an hour': lambda _: timedelta(hours=1),
            r'tomorrow': lambda _: timedelta(days=1),
            r'next week': lambda _: timedelta(days=7),
            r'at (\d{1,2}):(\d{2})': self._parse_specific_time,
            r'at (\d{1,2}) (am|pm)': self._parse_time_ampm
        }
        
        self.DEFAULT_DURATION = 30  # minutes

    def _extract_task(self, text: str) -> str:
        """Extract the main task using T5 model"""
        input_text = f"extract task: {text}"
        inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
        
        outputs = self.model.generate(
            inputs.input_ids,
            max_length=64,
            num_beams=4,
            early_stopping=True
        )
        
        task = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return task.strip()

    def _parse_specific_time(self, hours: str, minutes: str) -> timedelta:
        """Convert specific time (HH:MM) to timedelta from now"""
        now = datetime.now()
        target = now.replace(hour=int(hours), minute=int(minutes))
        if target < now:
            target = target + timedelta(days=1)
        return target - now

    def _parse_time_ampm(self, hour: str, meridiem: str) -> timedelta:
        """Convert time with AM/PM to timedelta from now"""
        hour = int(hour)
        if meridiem.lower() == 'pm' and hour != 12:
            hour += 12
        return self._parse_specific_time(str(hour), "0")

    def _extract_time_info(self, text: str) -> timedelta:
        """Extract time information primarily using regex patterns"""
        return self._extract_time_regex(text)

    def _extract_time_regex(self, text: str) -> timedelta:
        """Fallback regex-based time extraction"""
        for pattern, handler in self.time_patterns.items():
            match = re.search(pattern, text.lower())
            if match:
                return handler(*match.groups())
        return timedelta(minutes=self.DEFAULT_DURATION)

    def parse_reminder_text(self, statement: str) -> Dict[str, Any]:
        """Parse natural language statement into calendar event details"""
        # Extract the main task
        task = self._extract_task(statement)
        
        # Get current time as default
        start_time = datetime.now(timezone.utc)
        
        # Extract time information
        time_delta = self._extract_time_info(statement)
        start_time = start_time + time_delta
        
        # Create structured output
        return {
            'title': f"Reminder: {task}",
            'description': statement,
            'startTime': start_time.isoformat(),
            'endTime': (start_time + timedelta(minutes=self.DEFAULT_DURATION)).isoformat(),
            'timeZone': 'America/Denver',
            'reminder': 5
        }

    def get_entities(self, statement: str) -> Dict[str, list]:
        """Extract named entities using the model"""
        ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
        entities = {}
        
        try:
            results = ner_pipeline(statement)
            for result in results:
                entity_type = result['entity']
                if entity_type not in entities:
                    entities[entity_type] = []
                entities[entity_type].append(result['word'])
        except Exception as e:
            print(f"Error in entity extraction: {e}")
            
        return entities 

def process_text(text: str) -> Dict[str, Any]:
    """Process text and return parsed reminder details"""
    parser = ReminderParser()
    try:
        result = parser.parse_reminder_text(text)
        return {
            'title': result['title'],
            'description': result['description'],
            'startTime': result['startTime'],
            'endTime': result['endTime'],
            'timeZone': result['timeZone'],
            'reminder': result['reminder']
        }
    except Exception as e:
        print(f"Error processing text: {e}")
        raise

def main():
    """Interactive reminder parser"""
    try:
        print("Natural Language Reminder Parser")
        print("=" * 50)
        print("Enter your reminder text (or 'quit' to exit)")
        print("Example: 'remind me to call John in 2 hours'")
        print("=" * 50)
        
        parser = ReminderParser()
        
        while True:
            # Get user input
            statement = input("\nEnter reminder text: ").strip()
            
            # Check for exit command
            if statement.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
                
            # Skip empty input
            if not statement:
                print("Please enter a reminder text.")
                continue
                
            try:
                # Parse the reminder
                result = parser.parse_reminder_text(statement)
                
                # Get named entities
                entities = parser.get_entities(statement)
                
                # Print results
                print("\nParsed Reminder:")
                print(f"Title: {result['title']}")
                print(f"Start Time: {result['startTime']}")
                print(f"End Time: {result['endTime']}")
                print(f"Time Zone: {result['timeZone']}")
                print(f"Reminder: {result['reminder']} minutes before")
                
                if entities:
                    print("\nDetected Entities:")
                    for entity_type, values in entities.items():
                        print(f"{entity_type}: {', '.join(values)}")
                
                # Ask if the parsing is correct
                confirm = input("\nIs this correct? (y/n): ").strip().lower()
                if confirm == 'y':
                    print("Reminder parsed successfully!")
                else:
                    print("Please try rephrasing your reminder.")
                    
            except Exception as e:
                print(f"Error processing reminder: {e}")
                print("Please try again with different wording.")
                
    except Exception as e:
        print(f"Error initializing parser: {e}")
        
    finally:
        print("\nThank you for using the Reminder Parser!")

if __name__ == "__main__":
    main() 
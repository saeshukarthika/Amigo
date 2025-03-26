# Amigo - WhatsApp-based Conversational AI Assistant

## Overview

Amigo is a WhatsApp-based conversational AI assistant designed to help users manage tasks, set reminders, and achieve goals effortlessly. By leveraging Natural Language Processing (NLP), Amigo can process user inputs, generate relevant actions, and synchronize with Google Calendar for scheduling and notifications.

## Features

- **Task Management**: Create, update, and track tasks with simple WhatsApp messages.
- **Reminders & Notifications**: Set reminders and receive timely notifications via WhatsApp.
- **Goal Tracking**: Define and monitor progress on personal or professional goals.
- **Google Calendar Integration**: Sync tasks and events with Google Calendar for seamless scheduling.
- **Conversational UI**: User-friendly AI-driven conversation flow.

## Tech Stack

- **Python** - Backend logic and NLP processing
- **AWS Lambda** - Serverless computing for handling requests
- **API Gateway** - Secure API endpoints
- **DynamoDB** - NoSQL database for storing user data
- **AWS Bedrock (Llama)** - NLP model for text understanding and response generation
- **Hugging Face** - Additional NLP models and preprocessing
- **Twilio API** - WhatsApp integration for conversational interface

## Architecture

1. **User Interaction**: Messages are sent via WhatsApp.
2. **Twilio API**: Forwards user messages to AWS Lambda.
3. **NLP Processing**: AWS Bedrock (Llama) and Hugging Face models interpret messages.
4. **Action Execution**: Amigo processes tasks, updates reminders, and syncs with Google Calendar.
5. **Response Generation**: NLP formulates replies, sent back via Twilio.
6. **Data Persistence**: DynamoDB stores task and user information.

## Setup & Deployment

### Prerequisites

- AWS account with Lambda, API Gateway, DynamoDB, and Bedrock enabled.
- Twilio account for WhatsApp messaging.
- Google Calendar API access.

### Installation

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/amigo.git
   cd amigo
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up AWS services (Lambda, API Gateway, DynamoDB, Bedrock).
4. Configure Twilio API for WhatsApp integration.
5. Deploy to AWS Lambda using Serverless Framework or AWS SAM.
6. Link Google Calendar API for event synchronization.

## Usage

- Start a WhatsApp conversation with Amigo.
- Use natural language to create tasks, set reminders, or ask about upcoming events.
- Amigo will process requests and respond with relevant actions and confirmations.

## Future Enhancements

- Voice command support
- Multi-language processing
- Advanced analytics for goal tracking
- Smart suggestions based on user habits


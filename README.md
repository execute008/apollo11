# Apollo ElevenLabs Call Orchestrator

A Python-based call agent orchestrator that automatically calls contacts from Apollo.io using ElevenLabs AI agents to schedule appointments. The system uses a swarm pattern to efficiently manage multiple concurrent calls.

## 🎨 NEW: Interactive TUI (Text User Interface)

**Launch the interactive interface:**
```bash
python -m src.main tui
# or
apollo-tui  # after installation
```

The TUI provides a guided workflow for creating call campaigns:

1. **📋 Browse & Select Contacts** - Interactive Apollo contact browser with filtering
2. **📅 Configure Calendar** - Set up appointment time slots
3. **✍️  AI Script Composer** - Generate professional scripts using Claude or GPT
4. **🎯 Workflow Creator** - Review and configure complete campaign
5. **📊 Campaign Monitor** - Real-time progress tracking and results

[See full TUI Guide →](TUI_GUIDE.md)

## Features

- **🎨 Interactive TUI**: Visual workflow for campaign creation (NEW!)
- **🤖 AI Script Generation**: Generate call scripts with Claude or GPT (NEW!)
- **Apollo.io Integration**: Automatically fetch contacts with phone numbers
- **ElevenLabs AI Calling**: Use conversational AI agents to make calls
- **Agent Swarm Pattern**: Efficiently manage multiple concurrent calls
- **Smart Filtering**: Exclude contacts that already have appointments
- **Phone Validation**: Validate and format phone numbers automatically
- **Retry Logic**: Automatic retry for failed calls
- **Result Tracking**: Comprehensive logging and reporting
- **CSV Export**: Export campaign results to CSV
- **CLI Interface**: Easy-to-use command-line interface

## Architecture

The system consists of several key components:

1. **Apollo Client** (`src/clients/apollo_client.py`): Handles fetching and filtering contacts from Apollo.io
2. **ElevenLabs Client** (`src/clients/elevenlabs_client.py`): Manages AI-powered phone calls
3. **Call Agent** (`src/orchestrator/call_agent.py`): Individual agent responsible for a single call
4. **Agent Swarm** (`src/orchestrator/agent_swarm.py`): Manages multiple concurrent call agents
5. **Orchestrator** (`src/orchestrator/orchestrator.py`): Main coordinator that ties everything together

### Swarm Pattern

The swarm pattern allows the system to efficiently manage multiple concurrent calls:

- Each contact is assigned to a CallAgent
- CallAgents are managed by the AgentSwarm
- The swarm uses asyncio semaphores to limit concurrent calls
- Failed calls are automatically retried
- Results are aggregated and tracked

## Installation

### Prerequisites

- Python 3.9+
- Apollo.io API key
- ElevenLabs API key
- ElevenLabs Agent ID

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd apollo11
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install the package:
```bash
pip install -e .
```

4. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
APOLLO_API_KEY=your_apollo_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_AGENT_ID=your_agent_id_here

# Optional: For AI script generation in TUI
ANTHROPIC_API_KEY=your_anthropic_key  # For Claude
# OR
OPENAI_API_KEY=your_openai_key  # For GPT
LLM_PROVIDER=anthropic  # or 'openai'
```

5. Configure campaign settings in `config.yaml`:
```yaml
appointment:
  purpose: "Schedule a product demo"
  duration_minutes: 30

agent_prompt:
  first_message: |
    Hi, this is calling to schedule an appointment. Is this a good time?
```

## Usage

### Interactive TUI (Recommended)

The easiest way to create and manage campaigns is through the interactive TUI:

```bash
python -m src.main tui
```

The TUI provides a visual, step-by-step workflow:
1. Browse and select contacts from Apollo
2. Configure calendar appointment slots
3. Generate call scripts using AI (Claude or GPT)
4. Review and configure campaign settings
5. Monitor campaign execution in real-time

**[Read the full TUI Guide →](TUI_GUIDE.md)**

### CLI Commands

The orchestrator also provides several CLI commands for scriptable operations:

#### Launch TUI

Launch the interactive Text User Interface:

```bash
python -m src.main tui
```

This is the recommended way to create and manage campaigns with a visual workflow.

#### Run a Campaign

Run a full call campaign:

```bash
python -m src.main run
```

Options:
- `--limit, -n`: Maximum number of contacts to call
- `--include-with-appointments`: Include contacts that already have appointments
- `--output-dir, -o`: Directory to save results (default: ./results)
- `--dry-run`: Fetch contacts but don't make calls

Examples:
```bash
# Call up to 10 contacts
python -m src.main run --limit 10

# Dry run to see who would be called
python -m src.main run --dry-run

# Save results to custom directory
python -m src.main run --output-dir ./my_results
```

#### Fetch Contacts

Fetch contacts without calling (useful for testing filters):

```bash
python -m src.main fetch
```

Options:
- `--limit, -n`: Maximum number of contacts to fetch
- `--include-with-appointments`: Include contacts with appointments

#### View Configuration

Display current configuration:

```bash
python -m src.main config-info
```

#### Test Connections

Test API connections:

```bash
python -m src.main test-connection
```

### Programmatic Usage

You can also use the orchestrator programmatically:

```python
from src.orchestrator import CallOrchestrator

# Create orchestrator
orchestrator = CallOrchestrator()

# Fetch contacts
contacts = orchestrator.fetch_contacts(limit=10)

# Execute campaign
results = orchestrator.execute_campaign_sync(
    contacts=contacts,
    save_results=True
)

# Get appointments
appointments = orchestrator.get_appointments()
print(f"Scheduled {len(appointments)} appointments")
```

### Async Usage

For async applications:

```python
import asyncio
from src.orchestrator import CallOrchestrator

async def main():
    orchestrator = CallOrchestrator()
    contacts = orchestrator.fetch_contacts(limit=10)
    results = await orchestrator.execute_campaign(contacts)
    print(results)

asyncio.run(main())
```

## Configuration

### Environment Variables

Required:
- `APOLLO_API_KEY`: Apollo.io API key
- `ELEVENLABS_API_KEY`: ElevenLabs API key
- `ELEVENLABS_AGENT_ID`: ElevenLabs agent ID for calls

Optional:
- `MAX_CONCURRENT_CALLS`: Maximum concurrent calls (default: 5)
- `CALL_RETRY_ATTEMPTS`: Number of retry attempts (default: 3)
- `CALL_TIMEOUT_SECONDS`: Call timeout in seconds (default: 300)
- `LOG_LEVEL`: Logging level (default: INFO)

### Config File (config.yaml)

The `config.yaml` file allows you to configure:

#### Orchestrator Settings
```yaml
orchestrator:
  max_concurrent_calls: 5
  retry_attempts: 3
  retry_delay_seconds: 5
  call_timeout_seconds: 300
  batch_size: 50
```

#### Apollo Filters
```yaml
apollo:
  filters:
    has_phone: true
    has_appointments: false
    # Add custom filters based on Apollo API
```

#### ElevenLabs Configuration
```yaml
elevenlabs:
  agent:
    voice_id: null
    stability: 0.5
    similarity_boost: 0.75
  call:
    max_duration: 300
    record: true
```

#### Appointment Configuration
```yaml
appointment:
  purpose: "Schedule a product demo"
  duration_minutes: 30
  available_times:
    - "9:00 AM - 12:00 PM EST"
    - "2:00 PM - 5:00 PM EST"
```

#### Agent Prompt
```yaml
agent_prompt:
  system_prompt: |
    You are a professional sales representative calling to schedule an appointment.
    Be professional, concise, and respectful.

  first_message: |
    Hi, this is an automated call regarding scheduling an appointment.
    Is this a good time to talk briefly?
```

## Output

The orchestrator generates two types of output files:

### JSON Results
Comprehensive results in JSON format:
```json
{
  "total_contacts": 10,
  "completed": 8,
  "failed": 2,
  "appointments_scheduled": 5,
  "success_rate": 80.0,
  "appointment_rate": 50.0,
  "results": [...]
}
```

### CSV Summary
Tabular summary in CSV format:
```csv
contact_name,phone,company,status,call_id,duration,appointment_scheduled
John Doe,+15551234567,Acme Corp,completed,call_123,45.2,true
```

## Project Structure

```
apollo11/
├── src/
│   ├── __init__.py
│   ├── main.py                 # CLI entry point
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── apollo_client.py    # Apollo.io API client
│   │   └── elevenlabs_client.py # ElevenLabs API client
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── call_agent.py       # Individual call agent
│   │   ├── agent_swarm.py      # Swarm manager
│   │   └── orchestrator.py     # Main orchestrator
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py         # Configuration management
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # Logging utilities
│       └── phone_validator.py  # Phone validation
├── config.yaml                 # Main configuration file
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
└── README.md                  # This file
```

## API Documentation

### Apollo.io API

The system uses Apollo.io's People Search API to fetch contacts. Key features:

- Search people with various filters
- Filter by phone number availability
- Check appointment status
- Update contact records

See [Apollo.io API Documentation](https://docs.apollo.io/) for details.

### ElevenLabs API

The system uses ElevenLabs Conversational AI API for making calls:

- Create outbound calls
- Batch calling
- Real-time call status
- Call transcripts

See [ElevenLabs API Documentation](https://elevenlabs.io/docs) for details.

## Error Handling

The system includes comprehensive error handling:

- **Retry Logic**: Failed calls are automatically retried (configurable)
- **Phone Validation**: Invalid phone numbers are skipped
- **Rate Limiting**: Respects API rate limits with exponential backoff
- **Logging**: Detailed logging of all operations
- **Graceful Shutdown**: Handle Ctrl+C gracefully

## Best Practices

1. **Start Small**: Test with `--limit 5` before running large campaigns
2. **Use Dry Run**: Use `--dry-run` to preview contacts before calling
3. **Monitor Logs**: Check `logs/orchestrator.log` for detailed information
4. **Configure Agent**: Customize the ElevenLabs agent prompt for your use case
5. **Respect Rate Limits**: Adjust `max_concurrent_calls` based on your API limits
6. **Test Connections**: Run `test-connection` before starting campaigns

## Troubleshooting

### Common Issues

**Issue**: No contacts found
- Check Apollo.io filters in `config.yaml`
- Verify contacts have phone numbers
- Check appointment filtering

**Issue**: Calls failing
- Verify ElevenLabs API key and agent ID
- Check phone number format (should be E.164)
- Review logs for specific errors

**Issue**: Rate limit errors
- Reduce `max_concurrent_calls`
- Increase `retry_delay_seconds`

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

The project follows PEP 8 style guidelines:

```bash
black src/
flake8 src/
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
- Create an issue on GitHub
- Email: oskar@freye.tech

## Roadmap

- [ ] Add webhook support for real-time notifications
- [ ] Integrate with calendar systems (Google Calendar, Outlook)
- [ ] Add SMS fallback for failed calls
- [ ] Support for multiple languages
- [ ] Dashboard for monitoring campaigns
- [ ] A/B testing for different prompts
- [ ] Integration with CRM systems

## Acknowledgments

- Apollo.io for contact data API
- ElevenLabs for conversational AI platform
- Python asyncio for concurrent execution

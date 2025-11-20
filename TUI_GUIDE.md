# TUI (Text User Interface) Guide

## Overview

The Apollo ElevenLabs Call Orchestrator includes a powerful interactive TUI that provides a visual workflow for creating and managing call campaigns. The TUI guides you through the entire process from contact selection to campaign execution.

## Launching the TUI

There are two ways to launch the TUI:

### Method 1: Via CLI Command
```bash
python -m src.main tui
```

### Method 2: Direct Entry Point (after installation)
```bash
apollo-tui
```

### Method 3: Standalone Script
```bash
python -m src.tui_main
```

## TUI Workflow

The TUI provides a guided 5-step workflow:

### 1. Browse & Select Contacts 📋

**Purpose**: View and select contacts from Apollo.io to include in your campaign

**Features**:
- Real-time contact fetching from Apollo API
- Batch browsing with pagination (50 contacts per batch)
- Filter by name, company, or title
- Interactive selection/deselection
- Visual indicators for selected contacts
- Bulk select/deselect all

**Key Bindings**:
- `f` - Fetch contacts
- `a` - Select all contacts
- `n` - Deselect all contacts
- `c` - Continue to calendar configuration
- `ESC` - Go back

**Usage**:
1. Enter search filters (optional)
2. Click "Fetch Contacts" or press `f`
3. Browse through contacts using pagination
4. Click rows to toggle selection
5. Use "Select All" for bulk operations
6. Click "Continue" when ready

### 2. Configure Calendar Slots 📅

**Purpose**: Set up available appointment time slots

**Features**:
- Add multiple time slots
- Configure day(s), start/end times, timezone
- Set appointment duration
- Pre-populated with sensible defaults
- Edit or delete existing slots
- Load default business hour slots

**Key Bindings**:
- `a` - Add time slot
- `d` - Delete selected slot
- `c` - Continue to script composer
- `ESC` - Go back

**Usage**:
1. Review default slots (Monday-Friday, 9 AM-12 PM and 2 PM-5 PM EST)
2. Add custom slots if needed:
   - Select day(s) of the week
   - Enter start and end times
   - Select timezone
   - Set appointment duration
3. Delete unwanted slots by selecting and pressing `d`
4. Click "Continue" when calendar is configured

### 3. Compose Call Script (AI-Powered) ✍️

**Purpose**: Generate professional call scripts using AI

**Features**:
- AI-powered script generation (Claude or GPT)
- Customizable campaign parameters
- Multiple tone options (professional, friendly, consultative, etc.)
- Tabbed view of script sections:
  - Full script
  - Opening
  - Value proposition
  - Objection handling
  - Closing
  - Agent instructions
- Script refinement
- Template loading
- Save/export scripts

**Key Bindings**:
- `g` - Generate script with AI
- `r` - Refine script
- `c` - Continue to workflow creator
- `ESC` - Go back

**Usage**:
1. Fill in campaign configuration:
   - **Campaign Purpose**: "Schedule product demo for SaaS platform"
   - **Target Audience**: "CTOs and Technical Leads at B2B companies"
   - **Company/Product**: "TechCorp - AI-powered analytics platform"
   - **Value Proposition**: "Reduce data analysis time by 70%"
   - **Tone**: Select appropriate tone
2. Select LLM provider (Anthropic Claude or OpenAI GPT)
3. Click "Generate Script" or press `g`
4. Wait 10-20 seconds for AI generation
5. Review generated script in tabs
6. Edit directly in text areas if needed
7. Click "Refine Script" to improve based on feedback
8. Save and continue when satisfied

**AI Generation Details**:
The AI generates a comprehensive script including:
- Opening (first 10 seconds)
- Value proposition (20 seconds)
- Qualification questions
- Appointment request
- Objection handling for common objections:
  - "I'm busy"
  - "Not interested"
  - "Send me information"
  - "Call back later"
- Closing
- Voicemail script
- Agent behavior instructions

### 4. Create Campaign Workflow 🎯

**Purpose**: Review all configurations and create the final campaign

**Features**:
- Comprehensive review of all settings
- Tabbed summary view:
  - **Summary**: Overall campaign readiness
  - **Contacts**: Selected contacts list
  - **Calendar**: Configured time slots
  - **Script**: Script preview
- Campaign settings configuration:
  - Campaign name
  - Max concurrent calls (1-15)
  - Retry attempts (0-5)
  - Call timeout
  - Save results toggle
  - Update Apollo toggle
  - Record calls toggle
- Workflow save/load
- Test mode (1 contact)
- Estimated duration calculation

**Key Bindings**:
- `l` - Launch campaign
- `s` - Save workflow
- `ESC` - Go back

**Usage**:
1. Review the Summary tab for campaign readiness
2. Check all configurations in tabs
3. Enter a campaign name
4. Configure campaign settings:
   - Set concurrent calls (5 recommended for balanced performance)
   - Set retry attempts (3 recommended)
   - Set timeout (300 seconds / 5 minutes recommended)
5. Toggle options as needed
6. **Test first**: Click "Test with 1 Contact" to verify setup
7. **Save workflow**: Click "Save Workflow" to save for later
8. **Launch**: Click "Launch Campaign" when ready

**Campaign Readiness Checklist**:
- ✓ Contacts selected
- ✓ Calendar slots configured
- ✓ Script generated
- ✓ API keys configured
- ✓ Settings reviewed

### 5. Monitor Active Campaign 📊

**Purpose**: Real-time monitoring of campaign progress

**Features**:
- Live statistics dashboard:
  - Total contacts
  - Completed calls
  - In progress
  - Failed calls
  - Appointments scheduled
  - Success rate
  - Appointment rate
  - Elapsed time
- Visual progress bar
- Call details table with:
  - Contact name
  - Phone number
  - Current status
  - Call duration
  - Result
- Activity log with real-time updates
- Campaign controls:
  - Pause/Resume
  - Cancel
  - Export results
- Auto-scrolling log

**Key Bindings**:
- `p` - Pause campaign
- `r` - Resume campaign
- `x` - Cancel campaign
- `ESC` - Exit (after completion)

**Usage**:
1. Campaign starts automatically upon entry
2. Watch real-time statistics update
3. Monitor individual calls in the table
4. Review activity log for details
5. Pause if needed (calls in progress will complete)
6. Resume when ready
7. Cancel if necessary
8. Export results when complete
9. Results are auto-saved to `results/` directory

**Statistics Explained**:
- **Success Rate**: (Completed / Total) × 100%
- **Appointment Rate**: (Appointments / Total) × 100%
- **Elapsed Time**: Total campaign duration

## Key Features

### AI-Powered Script Generation

The TUI integrates with leading LLMs to generate professional call scripts:

**Supported Providers**:
- **Anthropic Claude** (Claude 3.5 Sonnet)
- **OpenAI** (GPT-4, GPT-4 Turbo)

**Generation Process**:
1. Analyzes campaign purpose and target audience
2. Incorporates company information and value proposition
3. Generates conversation flow optimized for AI voice agents
4. Creates objection handling responses
5. Produces voicemail script
6. Provides agent behavior instructions

**Customization**:
- Select tone (professional, friendly, consultative, direct, casual)
- Incorporate calendar availability automatically
- Refine based on feedback
- Edit any section directly

### Batch Contact Management

**Features**:
- Paginated browsing (50 contacts per batch)
- Advanced filtering
- Bulk selection operations
- Real-time Apollo integration
- Phone number validation
- Appointment status checking

**Filters**:
- Name search
- Company filter
- Title filter
- Custom Apollo filters

### Calendar Integration

**Flexibility**:
- Multiple time slots
- Different days of week
- Multiple timezones
- Variable appointment durations

**Smart Defaults**:
- Pre-configured business hours
- Monday-Friday availability
- 30-minute appointments
- EST timezone

### Workflow Persistence

**Save/Load**:
- Save complete workflow configurations
- Load previous campaigns
- Export campaign templates
- Share workflows with team

**Saved Data**:
- Contact selections
- Calendar configuration
- Generated scripts
- Campaign settings

## Global Key Bindings

These bindings work throughout the TUI:

- `q` - Quit application (prompts if campaign is running)
- `h` - Show help screen
- `ESC` - Go back to previous screen
- `Tab` - Navigate between UI elements
- `Enter` - Activate buttons/confirm selections
- `Arrow Keys` - Navigate lists and tables
- `Space` - Toggle checkboxes

## Configuration

### Environment Variables

Required for TUI operation:

```bash
# Apollo.io
APOLLO_API_KEY=your_apollo_api_key

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_AGENT_ID=your_agent_id

# LLM (for script generation)
ANTHROPIC_API_KEY=your_anthropic_key  # For Claude
# OR
OPENAI_API_KEY=your_openai_key  # For GPT

# LLM Configuration
LLM_PROVIDER=anthropic  # or 'openai'
LLM_MODEL=claude-3-5-sonnet-20241022  # or 'gpt-4'
```

### Color Themes

The TUI respects your terminal color scheme and provides:
- Dark mode optimized interface
- High contrast for accessibility
- Color-coded status indicators:
  - 🟢 Green: Success, ready, appointments
  - 🟡 Yellow: Warning, pending, test mode
  - 🔴 Red: Error, failed, cancelled
  - 🔵 Blue: Information, in progress

## Tips & Best Practices

### 1. Start Small
- Test with 1-5 contacts first
- Verify script quality
- Check calendar integration
- Validate API connections

### 2. Use AI Generation
- Be specific in campaign purpose
- Provide clear value proposition
- Select appropriate tone
- Review and refine generated scripts

### 3. Configure Calendar Strategically
- Offer multiple time slots for flexibility
- Consider timezone differences
- Match appointment duration to your needs
- Include buffer time between appointments

### 4. Monitor in Real-Time
- Watch for patterns in failures
- Adjust concurrent calls based on performance
- Pause if too many failures occur
- Export results frequently

### 5. Save Workflows
- Save successful configurations
- Reuse proven scripts
- Document what works
- Share with team members

## Troubleshooting

### TUI Won't Launch

**Issue**: Error when starting TUI

**Solutions**:
1. Check dependencies: `pip install textual textual-dev`
2. Verify Python version: 3.9+
3. Check terminal compatibility
4. Try different terminal emulator

### AI Generation Fails

**Issue**: Script generation errors

**Solutions**:
1. Verify API keys in `.env`
2. Check API credits/quota
3. Ensure network connectivity
4. Try different LLM provider
5. Check model availability

### Contacts Not Loading

**Issue**: Empty contact list

**Solutions**:
1. Verify Apollo API key
2. Check internet connection
3. Review Apollo filters
4. Ensure contacts have phone numbers
5. Check Apollo API rate limits

### Campaign Not Starting

**Issue**: Campaign fails to start

**Solutions**:
1. Verify ElevenLabs API key
2. Check ElevenLabs agent ID
3. Ensure agent is configured
4. Review campaign settings
5. Check API credits

## Advanced Usage

### Custom Workflows

Create specialized workflows by:
1. Saving different configurations for different audiences
2. Using templates for common scenarios
3. A/B testing different scripts
4. Segmenting contacts by attributes

### Batch Processing

For large contact lists:
1. Use batch browsing efficiently
2. Process in waves (50-100 contacts)
3. Monitor and adjust between batches
4. Export results after each batch

### Integration with Other Tools

Export results to:
- CRM systems (via CSV)
- Calendar applications (via API)
- Analytics platforms (via JSON)
- Reporting tools (via exports)

## Keyboard-Driven Workflow

Power users can navigate entirely with keyboard:

```
1. Launch TUI:           python -m src.main tui
2. Browse Contacts:      f (fetch), a (select all), c (continue)
3. Configure Calendar:   (use Tab/Enter to add slots), c (continue)
4. Generate Script:      g (generate), review, c (continue)
5. Review & Launch:      l (launch) or s (save)
6. Monitor:              p (pause), r (resume), x (cancel)
```

## Support

For issues or questions:
- Check this guide
- Review error messages in activity log
- Check API credentials
- Consult main README.md
- Create GitHub issue

## What's Next

Future TUI enhancements:
- Calendar API integration (Google, Outlook)
- Voice preview of scripts
- A/B testing interface
- Analytics dashboard
- Team collaboration features
- Webhook configuration
- Custom objection handling builder

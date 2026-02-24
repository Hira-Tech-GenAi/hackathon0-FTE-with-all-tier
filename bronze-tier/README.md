# 🤖 Personal AI Employee - Silver Tier

**Author:** Hira Khalid  
**Hackathon:** Personal AI Employee Hackathon 0  
**Tier:** Silver (Functional Assistant)

A multi-channel AI assistant that monitors Gmail, WhatsApp, and LinkedIn, automatically posts to social media, creates action plans, and includes human-in-the-loop approval workflows.

**Silver Tier Features:**
- ✅ Multiple Watcher scripts (Gmail + WhatsApp + LinkedIn)
- ✅ Automatic LinkedIn posting for business/sales
- ✅ Claude reasoning loop with Plan.md generation
- ✅ MCP server for external actions (email sending)
- ✅ Human-in-the-loop approval workflow
- ✅ Windows Task Scheduler integration
- ✅ All AI functionality as Agent Skills

## 📁 Project Structure

```
bronze-tier/
├── ai-employee-vault/
│   ├── Inbox/              # Drop files here to be processed
│   ├── Needs_Action/       # Files currently being processed
│   ├── Done/               # Completed files
│   ├── Plans/              # Generated action plans (Silver Tier)
│   ├── Pending_Approval/   # Awaiting human approval (Silver Tier)
│   ├── Approved/           # Approved actions (Silver Tier)
│   ├── Rejected/           # Rejected actions (Silver Tier)
│   ├── Logs/               # Audit logs (Silver Tier)
│   ├── Briefings/          # CEO briefings (Silver Tier)
│   ├── LinkedIn/           # LinkedIn posts (Silver Tier)
│   ├── WhatsApp/           # WhatsApp messages (Silver Tier)
│   ├── Dashboard.md        # System status & activity log
│   ├── Company_Handbook.md # AI employee guidelines
│   └── Business_Goals.md   # Business objectives (Silver Tier)
├── gmail_watcher.py        # Monitors Gmail inbox
├── whatsapp_watcher.py     # Monitors WhatsApp (Silver Tier)
├── linkedin_watcher.py     # Auto-posts to LinkedIn (Silver Tier)
├── orchestrator.py         # Approval workflow (Silver Tier)
├── task_scheduler.py       # Windows Task Scheduler (Silver Tier)
├── generate_briefing.py    # CEO briefings (Silver Tier)
├── mcp-servers/
│   └── email_mcp_server.py # Email MCP server (Silver Tier)
├── skills.py               # Agent skills (modular functions)
├── main_agent.py           # Core agent loop with OpenAI
├── filesystem_watcher.py   # Monitors Inbox folder
├── README.md               # This file
└── pyproject.toml          # Project dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- uv package manager
- OpenAI API key
- Optional: Gmail credentials, LinkedIn API, WhatsApp Web

### Installation

1. **Install dependencies with uv:**

```bash
uv sync
```

2. **Set your API keys in `.env`:**

```bash
# OpenAI
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Gmail (for gmail_watcher.py)
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password

# LinkedIn (for linkedin_watcher.py)
LINKEDIN_ACCESS_TOKEN=your-token
LINKEDIN_PERSON_URN=your-person-urn

# Email SMTP (for MCP server)
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Dry run mode (set to 'false' for production)
DRY_RUN=true
```

3. **Install Playwright (for WhatsApp watcher):**

```bash
uv add playwright
playwright install
```

## 📋 Silver Tier Features

### 1. Multiple Watchers

#### Gmail Watcher
Monitors Gmail for important emails and processes them automatically.

```bash
uv run python gmail_watcher.py
```

#### WhatsApp Watcher
Monitors WhatsApp Web for important messages (keywords: urgent, invoice, payment, etc.).

```bash
uv run python whatsapp_watcher.py
```

**Demo Mode:** If Playwright is not installed, create message files in `ai-employee-vault/WhatsApp/`:

```markdown
From: John Doe
Message: Urgent! Need help with the project ASAP.
```

#### LinkedIn Watcher
Automatically posts business updates to LinkedIn to generate sales.

```bash
uv run python linkedin_watcher.py
```

**Create LinkedIn post request:**
Drop a file in `Inbox/` with "linkedin" or "post" in the name:

```
Topic: New Service Launch
Context: We're excited to announce our new AI consulting service!
```

### 2. Automatic LinkedIn Posting

The LinkedIn watcher automatically:
- Detects post requests in the Inbox folder
- Generates professional business posts
- Posts to LinkedIn (or logs in demo mode)
- Respects daily post limits (default: 3/day)
- Maintains post intervals (default: 4 hours)

**Example Business Post Templates:**
- Achievement announcements
- Educational content
- Client success stories
- Industry insights
- Service announcements

### 3. Claude Reasoning Loop with Plan.md

For complex tasks, the AI automatically creates structured plans:

```bash
# Plan files are created in Plans/ folder
Plans/
└── PLAN_invoice_client_a_20260222_143022.md
```

**Plan.md Structure:**
```markdown
---
plan_id: PLAN_invoice_client_a_20260222_143022
created: 2026-02-22T14:30:22Z
status: pending
objective: Send invoice to Client A
---

# Action Plan

## Objective
Send invoice to Client A

## Steps
- [ ] Analyze the request and identify requirements
- [ ] Gather necessary information and resources
- [ ] Execute the required actions
- [ ] Verify completion and quality
- [ ] Document outcomes and move to Done
```

### 4. MCP Server for Email

The Email MCP server enables sending emails via Claude Code:

```bash
# Start the MCP server (used internally by orchestrator)
uv run python mcp-servers/email_mcp_server.py
```

**Configure in Claude Code:**
```json
{
  "mcpServers": {
    "email": {
      "command": "python",
      "args": ["path/to/email_mcp_server.py"]
    }
  }
}
```

### 5. Human-in-the-Loop Approval Workflow

Sensitive actions require human approval before execution:

**Approval Process:**
1. AI creates approval request in `Pending_Approval/`
2. Human reviews and moves file to `Approved/` or `Rejected/`
3. Orchestrator executes approved actions
4. Results logged to `Logs/`

**Example Approval Request:**
```markdown
---
type: approval_request
approval_id: EMAIL_SEND_20260222_143022
action_type: email_send
created: 2026-02-22T14:30:22Z
expires: 2026-02-22T23:59:59Z
status: pending
---

# Approval Required

**Action Type:** email_send
**Created:** 2026-02-22T14:30:22Z
**Reason:** Sensitive action requires human approval

---

## Details

- **to**: client@example.com
- **subject**: Invoice #1234
- **body**: Please find attached...

---

## Instructions

### To Approve
Move this file to the `/Approved` folder.

### To Reject
Move this file to the `/Rejected` folder.
```

**Start the Orchestrator:**
```bash
uv run python orchestrator.py
```

### 6. Windows Task Scheduler Integration

Schedule automated tasks:

```bash
# Install scheduled tasks
uv run python task_scheduler.py install

# View task status
uv run python task_scheduler.py status

# Remove scheduled tasks
uv run python task_scheduler.py uninstall

# Generate daily briefing manually
uv run python task_scheduler.py briefing

# Generate weekly briefing
uv run python task_scheduler.py briefing --weekly
```

**Scheduled Tasks:**
| Task | Schedule | Description |
|------|----------|-------------|
| Daily Briefing | 8:00 AM daily | Generate CEO briefing |
| Gmail Watcher | On logon | Start Gmail monitoring |
| WhatsApp Watcher | On logon | Start WhatsApp monitoring |
| LinkedIn Watcher | On logon | Start LinkedIn monitoring |
| Orchestrator | On logon | Start approval workflow |
| Weekly Audit | Monday 7:00 AM | Weekly business review |
| Cleanup | 2:00 AM daily | Clean old logs |

### 7. CEO Briefings

Automated daily and weekly briefings:

```bash
# Generate daily briefing
uv run python generate_briefing.py

# Generate weekly briefing
uv run python generate_briefing.py --weekly
```

**Briefing Location:** `ai-employee-vault/Briefings/`

## 🛠️ Available Skills

### Core Skills (Bronze Tier)

| Skill | Description | Parameters |
|-------|-------------|------------|
| `move_file` | Move files between folders | `source`, `destination` |
| `read_file` | Read file contents | `path` |
| `write_to_file` | Write content to file | `path`, `content`, `append` |
| `update_dashboard` | Update Dashboard.md | `status`, `action`, `file_name` |
| `summarize_and_plan` | Analyze and create action plan | `file_path` |
| `mark_as_done` | Complete task and archive | `file_path`, `summary` |

### Silver Tier Skills

| Skill | Description | Parameters |
|-------|-------------|------------|
| `create_plan` | Create Plan.md with objectives | `objective`, `file_path`, `steps` |
| `request_approval` | Request human approval | `action_type`, `details`, `reason` |
| `check_approval_status` | Check approval status | `approval_id` |
| `log_action` | Log action to audit log | `action_type`, `details`, `result` |
| `send_email_draft` | Create email draft | `to`, `subject`, `body`, `requires_approval` |
| `update_plan_step` | Update plan step | `plan_path`, `step_number`, `completed` |

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|----------|
| `OPENAI_API_KEY` | OpenAI API key | For AI mode | - |
| `OPENAI_MODEL` | OpenAI model | Optional | `gpt-4o-mini` |
| `GMAIL_ADDRESS` | Gmail address | Gmail watcher | - |
| `GMAIL_APP_PASSWORD` | Gmail app password | Gmail watcher | - |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn API token | LinkedIn watcher | - |
| `LINKEDIN_PERSON_URN` | LinkedIn person URN | LinkedIn watcher | - |
| `EMAIL_ADDRESS` | SMTP email address | Email MCP | - |
| `EMAIL_PASSWORD` | SMTP password | Email MCP | - |
| `DRY_RUN` | Dry run mode (no real actions) | Optional | `true` |
| `ORCHESTRATOR_CHECK_INTERVAL` | Orchestrator check interval (seconds) | Optional | `30` |
| `LINKEDIN_DAILY_POST_LIMIT` | Max LinkedIn posts per day | Optional | `3` |
| `WHATSAPP_DAILY_LIMIT` | Max WhatsApp messages per day | Optional | `50` |

### WhatsApp Keywords

Messages matching these keywords are processed:
- `urgent`, `asap`, `help`, `invoice`, `payment`, `order`
- `meeting`, `call`, `deadline`, `emergency`, `question`
- `price`, `cost`, `buy`, `purchase`, `service`, `project`

## 📊 Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SOURCES                             │
├─────────────────┬─────────────────┬─────────────────────────────┤
│     Gmail       │    WhatsApp     │     LinkedIn       │ Files  │
└────────┬────────┴────────┬────────┴─────────┬────────┴────┬─────┘
         │                 │                  │             │      
         ▼                 ▼                  ▼             ▼      
┌─────────────────────────────────────────────────────────────────┐
│                    WATCHERS (Perception)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ Gmail Watcher│ │WhatsApp Watch│ │LinkedIn Watch│            │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘            │
└─────────┼────────────────┼────────────────┼────────────────────┘
          │                │                │                      
          ▼                ▼                ▼                      
┌─────────────────────────────────────────────────────────────────┐
│                    OBSIDIAN VAULT (Memory)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ /Inbox │ /Needs_Action │ /Done │ /Plans │ /Logs          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ /Pending_Approval │ /Approved │ /Rejected │ /Briefings   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────┘
                                 │                                 
                                 ▼                                 
┌─────────────────────────────────────────────────────────────────┐
│                    REASONING (Claude/OpenAI)                    │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    main_agent.py                          │ │
│  │   Read → Think → Plan → Write → Request Approval          │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────┘
                                 │                                 
              ┌──────────────────┴───────────────────┐             
              ▼                                      ▼             
┌────────────────────────────┐    ┌────────────────────────────────┐
│    HUMAN-IN-THE-LOOP       │    │         ACTION LAYER           │
│  ┌──────────────────────┐  │    │  ┌─────────────────────────┐   │
│  │ Review Approval Files│──┼───▶│  │    MCP SERVERS          │   │
│  │ Move to /Approved    │  │    │  │  ┌──────┐ ┌──────────┐  │   │
│  └──────────────────────┘  │    │  │  │Email │ │ Browser  │  │   │
│                            │    │  │  │ MCP  │ │   MCP    │  │   │
└────────────────────────────┘    │  │  └──┬───┘ └────┬─────┘  │   │
                                  │  └─────┼──────────┼────────┘   │
                                  └────────┼──────────┼────────────┘
                                           │          │             
                                           ▼          ▼             
                                  ┌────────────────────────────────┐
                                  │     EXTERNAL ACTIONS           │
                                  │  Send Email │ Make Payment     │
                                  │  Post Social│ Update Calendar  │
                                  └────────────────────────────────┘
```

## 📝 Testing

### Test 1: LinkedIn Auto-Posting

1. Create a post request file:
```bash
echo "Topic: New Service Launch
Context: We're excited to announce our new AI consulting service! Helping businesses automate workflows." > ai-employee-vault/Inbox/linkedin_post_test.txt
```

2. Start LinkedIn watcher:
```bash
uv run python linkedin_watcher.py
```

3. Check `ai-employee-vault/LinkedIn/post_log.json` for logged posts.

### Test 2: WhatsApp Message Processing

1. Create a demo message:
```bash
cat > ai-employee-vault/WhatsApp/test_message.txt << EOF
From: John Doe
Message: Urgent! Need help with the project. Invoice required ASAP.
EOF
```

2. Start WhatsApp watcher:
```bash
uv run python whatsapp_watcher.py
```

3. Check `ai-employee-vault/Inbox/` for processed message.

### Test 3: Approval Workflow

1. Process a file that requires approval (email send):
```bash
uv run python main_agent.py ai-employee-vault/Inbox/test_message.txt
```

2. Check `ai-employee-vault/Pending_Approval/` for approval requests.

3. Move file to `Approved/` to execute.

4. Start orchestrator:
```bash
uv run python orchestrator.py
```

### Test 4: CEO Briefing

```bash
# Daily briefing
uv run python generate_briefing.py

# Weekly briefing
uv run python generate_briefing.py --weekly
```

Check `ai-employee-vault/Briefings/` for generated briefings.

### Test 5: Task Scheduler

```bash
# Install tasks
uv run python task_scheduler.py install

# Check status
uv run python task_scheduler.py status

# Generate briefing
uv run python task_scheduler.py briefing
```

## 🐛 Troubleshooting

### LinkedIn Watcher Not Posting
- Verify `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_PERSON_URN` in `.env`
- Check daily post limit (default: 3/day)
- Check post interval (default: 4 hours)
- Review `ai-employee-vault/LinkedIn/post_log.json`

### WhatsApp Watcher Not Detecting Messages
- Install Playwright: `uv add playwright && playwright install`
- For demo mode, create files in `ai-employee-vault/WhatsApp/`
- Check keyword matching in `whatsapp_watcher.py`

### Approval Workflow Not Working
- Ensure orchestrator is running: `uv run python orchestrator.py`
- Check `Pending_Approval/` folder for requests
- Move files to `Approved/` to execute
- Review logs in `ai-employee-vault/Logs/`

### MCP Server Errors
- Verify email credentials in `.env`
- Check DRY_RUN mode (set to `false` for real sends)
- Review email logs in `ai-employee-vault/Logs/email_*.json`

### Task Scheduler Issues (Windows)
- Run as Administrator to install tasks
- Check Task Scheduler for error details
- Verify Python path: `where python`

## 🎯 Next Steps (Gold Tier)

- [ ] Full Odoo integration via MCP
- [ ] Facebook/Instagram integration
- [ ] Twitter (X) integration
- [ ] Multiple MCP servers
- [ ] Weekly business audit with CEO briefing
- [ ] Error recovery and graceful degradation
- [ ] Ralph Wiggum loop for autonomous completion

## 📄 License

MIT License - Feel free to use and modify for your hackathon!

## 🤝 Contributing

This is a hackathon project. Contributions welcome!

---

**Built with ❤️ for Personal AI Employee Hackathon 0 - Silver Tier**

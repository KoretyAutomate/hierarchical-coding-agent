# Hierarchical 3-Tier Agent System

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  YOU (Project Sponsor)                                  │
│  Role: Final decision maker                             │
│  Actions:                                                │
│    - Approve/reject implementation plans                 │
│    - Review final test results                           │
│    - Make business decisions                             │
│    - Provide high-level requirements                     │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  CLAUDE CODE (Project Manager)                          │
│  Role: Workflow coordinator & quality assurance         │
│  Actions:                                                │
│    - Break down user requests into tasks                 │
│    - Coordinate between Project Lead and Project Member │
│    - Run tests and verification                          │
│    - Create GitHub PRs                                   │
│    - Ensure quality standards                            │
│    - Present results to user                             │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  PROJECT LEAD (Technical Brain)                         │
│  Model: Qwen3-Next-80B-A3B-Thinking-AWQ-4bit            │
│  Port: 8000                                              │
│  Role: Technical leadership & decision making            │
│  Actions:                                                │
│    - Analyze requirements deeply                         │
│    - Create detailed implementation plans                │
│    - Make architectural decisions                        │
│    - Review code from Project Member                    │
│    - Approve/reject implementations                      │
│    - Provide technical guidance                          │
│    - Conduct deep research for podcast workflow          │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│  PROJECT MEMBER (Developer)                             │
│  Model: qwen3-coder (via Ollama)                        │
│  Port: 11434                                             │
│  Role: Implementation & coding                           │
│  Actions:                                                │
│    - Implement code based on Project Lead's plans       │
│    - Write unit tests                                    │
│    - Fix bugs                                            │
│    - Refactor code                                       │
│    - Report progress to Project Lead for review         │
└─────────────────────────────────────────────────────────┘
```

## Workflow: Fully Autonomous (Option A)

### Complete Flow

```
1. USER REQUEST
   You: "Add database support to save research findings"
   ↓

2. CLAUDE (PM) - TASK BREAKDOWN
   Claude: Analyzes request, creates context
   ↓

3. PROJECT LEAD - PLANNING
   Project Lead: Creates detailed implementation plan
   Output:
   - Requirements analysis
   - Technical approach
   - File changes needed
   - Testing strategy
   - Success criteria
   ↓

4. USER CHECKPOINT #1 ✅
   You: Review and approve plan
   ↓

5. PROJECT MEMBER - IMPLEMENTATION
   Project Member: Implements the plan
   Output:
   - Code changes
   - Test files
   - Documentation
   ↓

6. PROJECT LEAD - CODE REVIEW
   Project Lead: Reviews implementation
   Output:
   - Code quality assessment
   - Issues/improvements needed
   - Decision: APPROVE or REQUEST_CHANGES
   ↓

7. CLAUDE (PM) - TESTING & VERIFICATION
   Claude: Runs tests, verifies functionality
   Output:
   - Test results
   - Integration check
   - Quality report
   ↓

8. USER CHECKPOINT #2 ✅
   You: Review results, approve for PR
   ↓

9. CLAUDE (PM) - PR CREATION
   Claude: Creates GitHub PR
   Output:
   - Feature branch
   - Comprehensive PR description
   - Ready for merge (awaiting your approval)
```

## System Components

### 1. Project Lead Server
**File**: `/home/korety/coding-agent/lead_server.py`
- FastAPI server with OpenAI-compatible API
- Port: 8000
- Memory: Capped at 50% GPU
- Purpose: Deep research, planning, decision-making

**Start:**
```bash
cd ~/coding-agent
./start_lead_transformers.sh
```

**Test:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/v1/models
```

### 2. Project Member
**Service**: Ollama
- Port: 11434
- Model: qwen3-coder:latest
- Purpose: Code implementation

**Check:**
```bash
ollama list
curl http://localhost:11434/v1/models
```

### 3. Hierarchical Orchestrator
**File**: `/home/korety/coding-agent/hierarchical_orchestrator.py`
- Coordinates the 3-tier workflow
- Manages checkpoints
- Logs workflow progress

**Usage:**
```bash
cd ~/coding-agent
python3 hierarchical_orchestrator.py "Your request here"
```

## Example Session

### Request
```
You: "Add error handling to the podcast search tool"
```

### Stage 1: Planning (Project Lead)
```
Project Lead creates plan:

IMPLEMENTATION PLAN
===================

1. Requirements Analysis:
   - Add try-catch blocks to search_tool function
   - Handle network timeouts
   - Handle API key missing
   - Handle empty results

2. Technical Approach:
   - Wrap httpx calls in try-except
   - Add specific error handlers
   - Return user-friendly error messages

3. File Changes:
   - podcast_crew.py: Modify search_tool function (lines 60-78)

4. Testing Strategy:
   - Test with invalid API key
   - Test with network timeout
   - Test with empty query

5. Success Criteria:
   - No unhandled exceptions
   - Graceful error messages
   - System continues running after errors
```

**→ YOU APPROVE** ✅

### Stage 2: Implementation (Project Member)
```
Project Member implements:
- Modified search_tool function
- Added error handling
- Created test cases
```

### Stage 3: Review (Project Lead)
```
Project Lead reviews code:

CODE REVIEW
===========

✓ Error handling implemented correctly
✓ Follows Python best practices
✓ All edge cases covered
✓ Error messages are user-friendly

Decision: APPROVE
```

### Stage 4: Testing (Claude)
```
Claude runs tests:

TEST RESULTS
============

✓ All tests pass
✓ Error handling works as expected
✓ No regressions detected
✓ Code quality: Good
```

**→ YOU APPROVE** ✅

### Stage 5: PR Creation (Claude)
```
Claude creates PR:
- Branch: feature/add-search-error-handling
- Tests: Passing
- Status: Ready for merge
```

## Configuration

### Memory Allocation
- **Project Lead**: 50% GPU memory
- **Project Member**: Managed by Ollama (efficient GGUF)
- **Total**: Safe for DGX Spark stability

### Ports
- **8000**: Project Lead
- **11434**: Project Member (Ollama)

### API Compatibility
Both servers use OpenAI-compatible API:
- `/v1/chat/completions`
- `/v1/models`
- Standard request/response format

## Benefits of This Architecture

### For You (User)
- ✅ Only approve at key checkpoints
- ✅ High-quality implementations (reviewed by Project Lead)
- ✅ Fully tested before PR
- ✅ Minimal involvement needed

### For Development Quality
- ✅ **Project Lead Thinking mode** for complex reasoning
- ✅ **Deep research capability** for podcast workflow
- ✅ **Code review by AI** before human review
- ✅ **Automated testing** by Claude

### For Efficiency
- ✅ Fully autonomous between checkpoints
- ✅ Parallel work possible
- ✅ Clear separation of concerns
- ✅ Audit trail in logs

## Integration with Podcast Workflow

Project Lead can also:
1. **Plan podcast research** - Deep analysis of topics
2. **Review research quality** - Validate sources
3. **Make editorial decisions** - Content direction
4. **Optimize workflow** - Process improvements

This creates a **unified brain** for both:
- Coding tasks (with Project Member)
- Podcast research tasks (with crew.ai agents)

## Troubleshooting

### Lead Server Won't Start
```bash
# Check logs
tail -f ~/coding-agent/logs/lead_transformers.log

# Check if port is in use
lsof -i :8000

# Restart
pkill -f lead_server
./start_lead_transformers.sh
```

### Member Not Responding
```bash
# Check Ollama
ollama list
ollama ps

# Restart Ollama
sudo systemctl restart ollama
```

### Memory Issues
```bash
# Check GPU memory
nvidia-smi

# Both models should stay under 50% combined
```

## Files Structure

```
~/coding-agent/
├── lead_server.py                 # Project Lead server
├── start_lead_transformers.sh     # Startup script
├── hierarchical_orchestrator.py   # Main orchestrator
├── orchestrator.py                # Task queue (for Project Member)
├── agents/
│   └── coding_agent.py            # Project Member agent
├── tools/
│   └── coding_tools.py            # Dev tools
├── config/
│   └── agent_config.yaml          # Configuration
└── logs/
    ├── lead_transformers.log      # Project Lead logs
    └── workflow_*.json            # Workflow logs
```

## Next Steps

1. **Wait for Project Lead to load** (~2-3 minutes)
2. **Test the system** with a simple request
3. **Integrate with podcast workflow**
4. **Start building autonomously!**

---

**Ready to use the 3-tier system!** 🚀

Project Lead provides the intelligence, Project Member does the work, Claude ensures quality, and you make the final decisions.

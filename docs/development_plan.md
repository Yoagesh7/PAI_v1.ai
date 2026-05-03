# PartnerAI - Development Plan & Roadmap

## Project Overview

This plan outlines a strategic approach to evolve PartnerAI from its current state to a production-ready, scalable, and secure productivity platform. The roadmap is divided into 6 phases with clear priorities and success criteria.

---

## Phase 1: Critical Security & Stability Fixes (Week 1-2)

> **Priority**: 🔴 CRITICAL  
> **Goal**: Address immediate security vulnerabilities and stability issues

### 1.1 Password Security Implementation

**Task**: Implement bcrypt password hashing

**Files to Modify**:
- [`memory.py`](file:///c:/Users/yo405/PartnerAI/memory.py)

**Changes**:
1. Add bcrypt to `requirements.txt`
2. Update `create_account()` to hash passwords before storage
3. Update `verify_user()` to use bcrypt comparison
4. Create migration script to hash existing passwords

**Estimated Effort**: 4-6 hours

---

### 1.2 Environment Variables for Credentials

**Task**: Move hardcoded credentials to environment variables

**Files to Modify**:
- [`web/app.py`](file:///c:/Users/yo405/PartnerAI/web/app.py#L15-L19)
- New: `.env.example` (template)
- New: `.env` (gitignored)

**Changes**:
1. Create `.env.example`:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FLASK_SECRET_KEY=your-secret-key
TELEGRAM_BOT_TOKEN=your-bot-token
```

2. Update `web/app.py` to use `os.getenv()`
3. Update `.gitignore` to exclude `.env`
4. Update `README.md` with setup instructions

**Estimated Effort**: 2-3 hours

---

### 1.3 Database Integrity Enhancements

**Task**: Enable foreign key constraints and add indexes

**Files to Modify**:
- [`memory.py`](file:///c:/Users/yo405/PartnerAI/memory.py#L7-L9)

**Changes**:
1. Update `get_db()` to enable foreign keys:
```python
def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

2. Add indexes in `init_db()`:
```python
cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_user_time ON chat_history(user_id, timestamp)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_tasks_user_date ON daily_tasks(user_id, created_at)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_group_members ON group_members(group_id, user_id)")
```

**Estimated Effort**: 2 hours

---

### 1.4 Fix Duplicate Function

**Task**: Remove duplicate `get_weekly_productivity()` function

**Files to Modify**:
- [`memory.py`](file:///c:/Users/yo405/PartnerAI/memory.py#L607-L640)

**Changes**:
1. Delete the duplicate function definition (lines 607-640)
2. Verify all imports still work

**Estimated Effort**: 30 minutes

---

## Phase 2: Code Quality & Architecture (Week 3-4)

> **Priority**: 🟠 HIGH  
> **Goal**: Improve maintainability and reduce technical debt

### 2.1 Refactor web/app.py

**Task**: Split monolithic `web/app.py` into modular structure

**New File Structure**:
```
web/
├── app.py (main entry point)
├── routes/
│   ├── __init__.py
│   ├── auth.py (login, signup, logout, onboarding)
│   ├── api.py (JSON API endpoints)
│   ├── pages.py (template routes)
│   └── group.py (team collaboration routes)
├── services/
│   ├── __init__.py
│   ├── ai_service.py (AI chat logic)
│   ├── task_service.py (task generation)
│   └── email_service.py (reminder emails)
└── middleware/
    ├── __init__.py
    └── auth_middleware.py (session checks)
```

**Migration Steps**:
1. Create new directory structure
2. Extract authentication routes to `auth.py`
3. Extract API routes to `api.py`
4. Extract business logic to `services/`
5. Update imports in `app.py`
6. Test all endpoints

**Estimated Effort**: 12-16 hours

---

### 2.2 Implement Structured Logging

**Task**: Replace print statements with Python logging

**Files to Modify**:
- All Python files with `print()` statements
- New: `logging_config.py`

**Changes**:
1. Create `logging_config.py`:
```python
import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('partnerai.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
```

2. Replace all `print()` with `logger.info()`, `logger.error()`, etc.
3. Add log rotation

**Estimated Effort**: 6-8 hours

---

### 2.3 Add Type Hints

**Task**: Add type annotations to improve code clarity

**Files to Modify**:
- [`memory.py`](file:///c:/Users/yo405/PartnerAI/memory.py)
- [`smart_blocks.py`](file:///c:/Users/yo405/PartnerAI/smart_blocks.py)
- [`habit_intelligence.py`](file:///c:/Users/yo405/PartnerAI/habit_intelligence.py)

**Example**:
```python
from typing import Optional, List, Dict, Tuple

def get_user(user_id: int) -> Optional[Tuple]:
    ...

def create_block(user_id: int, block_type: str, title: str, 
                 content: str, metadata: Optional[Dict] = None) -> Optional[int]:
    ...
```

**Estimated Effort**: 8-10 hours

---

## Phase 3: Testing Infrastructure (Week 5-6)

> **Priority**: 🟡 MEDIUM  
> **Goal**: Establish automated testing to prevent regressions

### 3.1 Unit Tests for Core Functions

**Task**: Write unit tests for critical functions

**New Files**:
- `tests/__init__.py`
- `tests/test_memory.py`
- `tests/test_auth.py`
- `tests/test_smart_blocks.py`
- `tests/conftest.py` (pytest fixtures)

**Test Coverage Goals**:
- `memory.py`: 80% coverage
- `smart_blocks.py`: 70% coverage
- Authentication flows: 90% coverage

**Example Test**:
```python
# tests/test_memory.py
import pytest
from memory import create_account, verify_user, get_user

def test_create_account_success():
    user_id = create_account("testuser123", "password", "test@example.com")
    assert user_id is not None
    
def test_create_account_duplicate():
    create_account("duplicate", "pass", "email@test.com")
    result = create_account("duplicate", "pass2", "other@test.com")
    assert result is None

def test_verify_user_correct_password():
    user_id = verify_user("testuser123", "password")
    assert user_id is not None
    
def test_verify_user_wrong_password():
    user_id = verify_user("testuser123", "wrongpassword")
    assert user_id is None
```

**Run Command**: `pytest tests/ -v --cov=. --cov-report=html`

**Estimated Effort**: 16-20 hours

---

### 3.2 Integration Tests for AI Features

**Task**: Test AI integration with mocked responses

**New Files**:
- `tests/test_ai_integration.py`

**Example**:
```python
from unittest.mock import patch, MagicMock
from ollama_utils import safe_ollama_chat, OllamaConnectionError

@patch('ollama.chat')
def test_ai_chat_success(mock_chat):
    mock_chat.return_value = {'message': {'content': 'Test response'}}
    result = safe_ollama_chat('phi3', [{'role': 'user', 'content': 'Hello'}])
    assert result['message']['content'] == 'Test response'

def test_ai_connection_error():
    with pytest.raises(OllamaConnectionError):
        # Assuming Ollama is not running
        safe_ollama_chat('invalid-model', [{'role': 'user', 'content': 'Test'}])
```

**Estimated Effort**: 8-10 hours

---

### 3.3 End-to-End Tests

**Task**: Test complete user workflows

**Scenarios**:
1. **User Registration → Onboarding → First Task**
2. **Login → Create Group → Invite Member → Assign Task**
3. **Daily Task Generation → Completion → Streak Update**

**Tool**: Selenium or Playwright for web UI testing

**Estimated Effort**: 12-16 hours

---

## Phase 4: Performance & Scalability (Week 7-9)

> **Priority**: 🟡 MEDIUM  
> **Goal**: Prepare for production scaling

### 4.1 Database Migration to PostgreSQL

**Task**: Move from SQLite to PostgreSQL

**New Files**:
- `migrations/001_initial_schema.sql`
- `migrations/002_migrate_data.py`
- `db_config.py`

**Steps**:
1. Install `psycopg2-binary`
2. Set up PostgreSQL locally (Docker recommended)
3. Create migration scripts
4. Update `memory.py` to support both SQLite and PostgreSQL
5. Add database URL to `.env`

**Estimated Effort**: 20-24 hours

---

### 4.2 Implement Response Caching

**Task**: Cache AI responses to reduce latency

**New Files**:
- `cache_manager.py`

**Changes**:
1. Add Redis to infrastructure
2. Cache common AI queries (e.g., "What is AI?")
3. Implement cache invalidation strategy

**Example**:
```python
import redis
import hashlib

cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

def cached_ai_chat(model, messages, ttl=3600):
    cache_key = hashlib.md5(str(messages).encode()).hexdigest()
    cached = cache.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    response = safe_ollama_chat(model, messages)
    cache.setex(cache_key, ttl, json.dumps(response))
    return response
```

**Estimated Effort**: 8-12 hours

---

### 4.3 Add Rate Limiting

**Task**: Protect against abuse

**Changes**:
1. Install `Flask-Limiter`
2. Add rate limits to auth and API routes
3. Implement IP-based and user-based limits

**Example**:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    ...
```

**Estimated Effort**: 4-6 hours

---

## Phase 5: Feature Enhancements (Week 10-12)

> **Priority**: 🟢 LOW  
> **Goal**: Improve user experience and add requested features

### 5.1 Smart Blocks UI Integration

**Task**: Create web interface for Smart Blocks system

**New Files**:
- `web/templates/smart_blocks.html`
- `web/static/css/smart_blocks.css`
- `web/static/js/smart_blocks.js`

**Features**:
- Visual block editor
- Drag-and-drop relationship builder
- Network graph visualization (using D3.js or Cytoscape.js)

**Estimated Effort**: 24-32 hours

---

### 5.2 Enhanced Habit Analytics Dashboard

**Task**: Create comprehensive habit tracking UI

**New Files**:
- `web/templates/habits_dashboard.html`
- `web/static/js/charts.js`

**Features**:
- Heatmap of habit completions
- Failure analysis charts
- Optimal timing suggestions
- Goal-to-habit mapping visualization

**Estimated Effort**: 20-24 hours

---

### 5.3 Mobile Responsive Improvements

**Task**: Enhance mobile experience

**Changes**:
- Update CSS for better mobile layouts
- Optimize touch interactions
- Add Progressive Web App (PWA) features

**Estimated Effort**: 12-16 hours

---

## Phase 6: Production Readiness (Week 13-15)

> **Priority**: 🟢 LOW  
> **Goal**: Deploy to production environment

### 6.1 Docker Containerization

**Task**: Create Docker setup

**New Files**:
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/partnerai
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      - ollama
      
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: partnerai
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      
  redis:
    image: redis:7-alpine
    
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
      
volumes:
  postgres_data:
  ollama_data:
```

**Estimated Effort**: 8-12 hours

---

### 6.2 CI/CD Pipeline

**Task**: Automate testing and deployment

**New Files**:
- `.github/workflows/test.yml`
- `.github/workflows/deploy.yml`

**GitHub Actions Workflow**:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov
      - name: Security audit
        run: bandit -r . -ll
```

**Estimated Effort**: 6-8 hours

---

### 6.3 Monitoring & Observability

**Task**: Add production monitoring

**Tools**:
- Prometheus (metrics)
- Grafana (dashboards)
- Sentry (error tracking)

**New Files**:
- `prometheus.yml`
- `grafana/dashboards/partnerai.json`

**Estimated Effort**: 12-16 hours

---

## Verification Plan

### Security Verification

**1. Password Hashing**
- [ ] Manual: Create new account, verify password is hashed in database
- [ ] Automated: `pytest tests/test_auth.py::test_password_hashing`

**2. Environment Variables**
- [ ] Manual: Remove `.env` file, verify app fails to start
- [ ] Manual: Check that `.env` is in `.gitignore`

**3. SQL Injection**
- [ ] Automated: `pytest tests/test_security.py::test_sql_injection_attempts`

---

### Functionality Verification

**4. User Onboarding**
- [ ] Manual: Complete onboarding flow in browser
- [ ] Verify AI generates tasks
- [ ] Verify redirect to chat on completion

**5. Task Management**
- [ ] Manual: Use `/daily` command
- [ ] Verify tasks appear in productivity page
- [ ] Complete a task, verify streak increases

**6. Group Collaboration**
- [ ] Manual: Create group as user 1
- [ ] Get invite code
- [ ] Join as user 2 with invite code
- [ ] Verify both users see group

**7. AI Chat**
- [ ] Manual: Send message in chat
- [ ] Verify AI response appears
- [ ] Check chat history persists after refresh

---

### Performance Verification

**8. Load Testing**
- [ ] Automated: `locust -f tests/load_test.py --host http://localhost:5000`
- [ ] Target: 100 concurrent users
- [ ] Success criteria: < 2s response time for 95% of requests

**9. Database Performance**
- [ ] Automated: `pytest tests/test_performance.py::test_query_times`
- [ ] All queries complete < 100ms

---

### Compatibility Verification

**10. Cross-Browser Testing**
- [ ] Manual: Test on Chrome, Firefox, Safari, Edge
- [ ] Verify all features work on each browser

**11. Mobile Testing**
- [ ] Manual: Test on iOS Safari and Android Chrome
- [ ] Verify responsive design

---

## Success Criteria

### Phase 1 Success
- [ ] All passwords in database are hashed
- [ ] No credentials in source code
- [ ] Foreign keys enforced
- [ ] No duplicate functions

### Phase 2 Success
- [ ] `web/app.py` < 500 lines
- [ ] All modules have type hints
- [ ] Structured logging in place
- [ ] Log files rotate daily

### Phase 3 Success
- [ ] 80% overall test coverage
- [ ] All tests passing
- [ ] CI pipeline running on every commit

### Phase 4 Success
- [ ] PostgreSQL successfully running
- [ ] Redis caching implemented
- [ ] Rate limiting active on all auth routes
- [ ] Sub-second response times for cached queries

### Phase 5 Success
- [ ] Smart Blocks UI complete and functional
- [ ] Habit dashboard with charts
- [ ] Mobile score > 90 on Lighthouse

### Phase 6 Success
- [ ] Docker Compose brings up full stack
- [ ] CI/CD deploying to staging environment
- [ ] Monitoring dashboards showing metrics
- [ ] Zero critical vulnerabilities in security scan

---

## Timeline Summary

| Phase | Duration | Effort | Dependencies |
|-------|----------|--------|--------------|
| **Phase 1** | Week 1-2 | ~17 hours | None |
| **Phase 2** | Week 3-4 | ~35 hours | Phase 1 complete |
| **Phase 3** | Week 5-6 | ~44 hours | Phase 2 complete |
| **Phase 4** | Week 7-9 | ~42 hours | Phase 3 complete |
| **Phase 5** | Week 10-12 | ~62 hours | Phase 4 complete |
| **Phase 6** | Week 13-15 | ~32 hours | Phase 5 complete |
| **Total** | 15 weeks | ~232 hours | Sequential |

---

## Risk Assessment

### High Risk
- **Database Migration**: Complex, high chance of data loss
  - Mitigation: Extensive backups, staged migration, rollback plan

- **Large Refactor**: Breaking changes likely
  - Mitigation: Feature flags, comprehensive tests first

### Medium Risk
- **Performance Degradation**: New caching layer may introduce bugs
  - Mitigation: Load testing before production

### Low Risk
- **UI Improvements**: Isolated changes
  - Mitigation: User feedback sessions

---

## Resource Requirements

### Developer Time
- **Solo Developer**: 15 weeks full-time OR 6 months part-time (20 hrs/week)
- **Team of 2**: 8-10 weeks

### Infrastructure
- **Development**: Personal machine (16GB RAM, GPU for Ollama)
- **Staging**: DigitalOcean Droplet ($20/month)
- **Production**: AWS/GCP ($100-200/month)

### Tools & Services
- **GitHub**: Free for public repos
- **Docker**: Free
- **PostgreSQL**: Free
- **Redis**: Free
- **Ollama**: Free (local)

---

## Post-Launch Roadmap

### Q2 2026
- [ ] Mobile apps (React Native)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User analytics dashboard

### Q3 2026
- [ ] Multi-language support
- [ ] Advanced AI features (voice chat)
- [ ] Social features expansion

### Q4 2026
- [ ] Enterprise features (SSO, RBAC)
- [ ] Data export/import
- [ ] Third-party integrations (Notion, Todoist)

---

## Document Version
- **Version**: 1.0
- **Date**: 2026-01-21
- **Status**: Approved for Implementation
- **Next Review**: After Phase 1 completion

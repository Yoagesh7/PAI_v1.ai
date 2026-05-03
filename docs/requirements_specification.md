# PartnerAI - Requirements Specification

## Executive Summary

**PartnerAI** is an AI-powered personal productivity and growth companion that combines habit tracking, intelligent task management, team collaboration, and personalized coaching. The system uses local AI models (via Ollama) to provide privacy-focused mentorship through both a Telegram bot and a comprehensive web dashboard.

---

## 1. System Overview

### 1.1 Purpose
PartnerAI aims to help users achieve their personal and professional goals through:
- Personalized AI mentorship
- Intelligent habit tracking and analysis
- Smart task management with AI-generated recommendations
- Team collaboration features
- Productivity analytics and weekly coaching reports

### 1.2 Target Users
- **Primary**: Individuals seeking personal growth, skill development, or productivity improvement
- **Secondary**: Small teams working on collaborative projects
- **Tertiary**: Students and professionals managing learning goals

---

## 2. Functional Requirements

### 2.1 User Management & Authentication

#### FR-UM-001: User Registration
- **Description**: Users can create accounts with username, password, and email
- **Priority**: HIGH
- **Status**: ✅ Implemented

#### FR-UM-002: User Login
- **Description**: Secure authentication system with session management
- **Priority**: HIGH
- **Status**: ✅ Implemented

#### FR-UM-003: Multi-Platform Access
- **Description**: Users can access via web dashboard or Telegram bot
- **Priority**: HIGH
- **Status**: ✅ Implemented

---

### 2.2 Onboarding & Personalization

#### FR-ON-001: User Onboarding Wizard
- **Description**: Multi-step wizard collecting:
  - Name and age
  - Primary goal/career objective
  - Work schedule and free time availability
- **Priority**: HIGH
- **Status**: ✅ Implemented
- **Location**: [`web/templates/onboarding.html`](file:///c:/Users/yo405/PartnerAI/web/templates/onboarding.html), [`web/app.py`](file:///c:/Users/yo405/PartnerAI/web/app.py#L163-L233)

#### FR-ON-002: Initial Task Generation
- **Description**: AI generates 3 starter tasks based on user goal and schedule
- **Priority**: HIGH
- **Status**: ✅ Implemented
- **AI Model**: Phi3
- **Fallback**: Template tasks if AI unavailable

---

### 2.3 AI Chat & Conversational Interface

#### FR-CH-001: Conversational AI Mentor
- **Description**: Natural language chat interface with context-aware responses
- **Priority**: CRITICAL
- **Status**: ✅ Implemented
- **Features**:
  - Personalized responses based on user profile
  - Context retention through chat history
  - Markdown formatting support
  - Streaming responses for better UX
- **Location**: [`web/app.py`](file:///c:/Users/yo405/PartnerAI/web/app.py#L494-L936), [`partnerai.py`](file:///c:/Users/yo405/PartnerAI/partnerai.py#L53-L565)

#### FR-CH-002: Command System
**Implemented Commands**:
- `/custom [tasks]` - Set custom tasks
- `/reminder [time] [message]` - Schedule email reminders
- `/reset` - Wipe user data and restart onboarding
- `/report` - View productivity statistics
- `/daily` - Generate AI-powered daily tasks
- `/article` - Generate personalized motivational articles
- `/news` - Fetch curated news based on user goals
- `/question [query]` - Ask general knowledge questions
- `/help [decision]` - Get decisive recommendations
- `/mt` - Receive motivational content
- `/task [topic]` - Set daily learning topic

**Priority**: HIGH
**Status**: ✅ Implemented

---

### 2.4 Smart Task Management

#### FR-TM-001: Daily Task Generation
- **Description**: AI generates 3-5 daily tasks aligned with user goals
- **Priority**: HIGH
- **Status**: ✅ Implemented
- **Endpoint**: `/api/chat` POST with `/daily` command
- **Storage**: `daily_tasks` table

#### FR-TM-002: Task Completion Tracking
- **Description**: Track task status (pending/in-progress/completed)
- **Priority**: HIGH
- **Status**: ✅ Implemented

#### FR-TM-003: Streak Tracking
- **Description**: Monitor consecutive days of task completion
- **Priority**: MEDIUM
- **Status**: ✅ Implemented
- **Database**: `users` table columns: `streak`, `last_active_date`, `tasks_completed`

---

### 2.5 Habit Intelligence System

#### FR-HI-001: Habit Failure Analysis
- **Description**: Analyze why specific habits are failing using AI
- **Priority**: HIGH
- **Status**: ✅ Implemented
- **Function**: [`habit_intelligence.analyze_habit_failures()`](file:///c:/Users/yo405/PartnerAI/habit_intelligence.py)
- **Output**: Failure patterns, success rate, recommendations

#### FR-HI-002: Optimal Timing Detection
- **Description**: Determine best time for habit completion based on historical data
- **Priority**: MEDIUM
- **Status**: ✅ Implemented
- **Function**: [`habit_intelligence.detect_optimal_timing()`](file:///c:/Users/yo405/PartnerAI/habit_intelligence.py)

#### FR-HI-003: Habit-to-Goal Mapping
- **Description**: Build dependency graph linking habits to user goals
- **Priority**: MEDIUM
- **Status**: ✅ Implemented
- **Function**: [`habit_intelligence.map_habits_to_goals()`](file:///c:/Users/yo405/PartnerAI/habit_intelligence.py)

#### FR-HI-004: Weekly Insights
- **Description**: Generate AI-powered weekly habit analysis
- **Priority**: HIGH
- **Status**: ✅ Implemented
- **Function**: [`habit_intelligence.generate_weekly_insights()`](file:///c:/Users/yo405/PartnerAI/habit_intelligence.py)

#### FR-HI-005: Auto-Adjust Habits
- **Description**: Suggest automatic adjustments based on failure analysis
- **Priority**: LOW
- **Status**: ✅ Implemented

---

### 2.6 Smart Blocks System

#### FR-SB-001: Block Types
**Supported Block Types**:
- 💡 **Idea Block**: Startup ideas, brainstorming
- ✅ **Task Block**: Daily/weekly actionable items
- 📘 **Learning Block**: Insights and learnings
- 🔁 **Habit Block**: Habit tracking with streaks
- 📊 **Reflection Block**: Weekly self-review

**Priority**: MEDIUM
**Status**: ✅ Implemented
**Location**: [`smart_blocks.py`](file:///c:/Users/yo405/PartnerAI/smart_blocks.py)

#### FR-SB-002: Block Relationships
- **Description**: Link blocks with relationships (related, depends_on, part_of, leads_to, inspired_by)
- **Priority**: MEDIUM
- **Status**: ✅ Implemented
- **Database**: `block_relationships` table

#### FR-SB-003: AI Block Suggestions
- **Description**: Suggest related blocks based on content similarity
- **Priority**: LOW
- **Status**: ✅ Implemented
- **Function**: [`smart_blocks.suggest_related_blocks()`](file:///c:/Users/yo405/PartnerAI/smart_blocks.py)

#### FR-SB-004: Network Analysis
- **Description**: Analyze block network to find patterns and isolated blocks
- **Priority**: LOW
- **Status**: ✅ Implemented

---

### 2.7 Team Collaboration

#### FR-TC-001: Group Creation
- **Description**: Team leaders can create groups with project name and deadline
- **Priority**: HIGH
- **Status**: ✅ Implemented
- **Endpoint**: `/api/group/create_or_join` POST

#### FR-TC-002: Invite System
- **Description**: Generate shareable 8-character invite codes
- **Priority**: HIGH
- **Status**: ✅ Implemented
- **Function**: [`memory.get_or_create_invite_code()`](file:///c:/Users/yo405/PartnerAI/memory.py#L414-L427)

#### FR-TC-003: AI Task Assignment
- **Description**: AI automatically assigns tasks to team members based on project goal
- **Priority**: MEDIUM
- **Status**: ✅ Implemented
- **Location**: [`web/app.py`](file:///c:/Users/yo405/PartnerAI/web/app.py#L373-L424)

#### FR-TC-004: Group Chat
- **Description**: Team chat with AI mentor participation
- **Priority**: HIGH
- **Status**: ✅ Implemented
- **Database**: `group_chat_messages` table

#### FR-TC-005: Task Status Updates
- **Description**: Track task status (PENDING, IN_PROGRESS, DONE)
- **Priority**: HIGH
- **Status**: ✅ Implemented

---

### 2.8 Productivity Analytics

#### FR-PA-001: Weekly Productivity Chart
- **Description**: 7-day visualization of completed tasks
- **Priority**: HIGH
- **Status**: ✅ Implemented
- **Function**: [`memory.get_weekly_productivity()`](file:///c:/Users/yo405/PartnerAI/memory.py#L607-L640)
- **Endpoint**: `/api/stats` GET

#### FR-PA-002: Progress Scoring
- **Description**: Calculate progress score (0-100) based on habits, tasks, engagement
- **Priority**: MEDIUM
- **Status**: ✅ Implemented
- **Function**: [`coach_engine.calculate_progress_score()`](file:///c:/Users/yo405/PartnerAI/coach_engine.py)

#### FR-PA-003: Strengths & Weaknesses Analysis
- **Description**: AI-driven analysis of user performance
- **Priority**: MEDIUM
- **Status**: ✅ Implemented
- **Function**: [`coach_engine.identify_strengths_weaknesses()`](file:///c:/Users/yo405/PartnerAI/coach_engine.py)

#### FR-PA-004: Weekly Coaching Report
- **Description**: Comprehensive weekly report with strategic recommendations
- **Priority**: HIGH
- **Status**: ✅ Implemented
- **Function**: [`coach_engine.create_weekly_report()`](file:///c:/Users/yo405/PartnerAI/coach_engine.py)

---

### 2.9 Reminders & Notifications

#### FR-RN-001: Email Reminders
- **Description**: Schedule email reminders with AI-generated motivational content
- **Priority**: MEDIUM
- **Status**: ✅ Implemented
- **Features**:
  - Parse natural language time (e.g., "10m", "at 5pm")
  - AI-enhanced email content in various styles (Stoic, High Energy, Zen, Scientific)
  - Background email scheduling
- **Location**: [`web/app.py`](file:///c:/Users/yo405/PartnerAI/web/app.py#L549-L636)

#### FR-RN-002: Telegram Reminders
- **Description**: Schedule Telegram bot reminders
- **Priority**: MEDIUM
- **Status**: ✅ Implemented
- **Location**: [`partnerai.py`](file:///c:/Users/yo405/PartnerAI/partnerai.py#L22-L34)

---

### 2.10 Focus Mode & Productivity Tools

#### FR-FM-001: Focus Mode Timer
- **Description**: Distraction-free productivity timer
- **Priority**: MEDIUM
- **Status**: ✅ Implemented
- **Page**: [`web/templates/focus_mode.html`](file:///c:/Users/yo405/PartnerAI/web/templates/focus_mode.html)

#### FR-FM-002: Music Integration
- **Description**: Background music during focus sessions
- **Priority**: LOW
- **Status**: ✅ Implemented
- **Storage**: `song/` directory

#### FR-FM-003: Custom Wallpapers
- **Description**: Selectable background wallpapers for focus mode
- **Priority**: LOW
- **Status**: ✅ Implemented
- **Storage**: `wallpaper/` directory

#### FR-FM-004: Reward System
- **Description**: Earn rewards (flowers, badges) for completed sessions
- **Priority**: LOW
- **Status**: ✅ Implemented
- **Database**: `user_rewards` table

---

### 2.11 Content Generation

#### FR-CG-001: Daily Articles
- **Description**: AI-generated motivational articles with book recommendations
- **Priority**: MEDIUM
- **Status**: ✅ Implemented
- **Command**: `/article`

#### FR-CG-002: Curated News
- **Description**: Fetch Google News RSS feed filtered by user goals
- **Priority**: LOW
- **Status**: ✅ Implemented
- **Command**: `/news`
- **Source**: Google News India RSS

---

## 3. Non-Functional Requirements

### 3.1 Performance

#### NFR-PF-001: AI Response Time
- **Requirement**: AI chat responses should stream within 5 seconds
- **Status**: ⚠️ Dependent on Ollama performance
- **Mitigation**: Streaming responses, background task generation

#### NFR-PF-002: Database Query Efficiency
- **Requirement**: All database queries complete within 100ms
- **Status**: ✅ Using indexed queries and connection pooling

#### NFR-PF-003: Concurrent Users
- **Target**: Support 50+ concurrent web users
- **Status**: ✅ Flask with SQLite, thread-safe connections

---

### 3.2 Security

#### NFR-SC-001: Password Storage
- **Requirement**: Plain text passwords (⚠️ **SECURITY RISK**)
- **Current**: No hashing implemented
- **Recommendation**: Implement bcrypt/argon2 hashing

#### NFR-SC-002: Session Management
- **Status**: ✅ Flask session with secret key
- **Location**: [`web/app.py`](file:///c:/Users/yo405/PartnerAI/web/app.py#L93)

#### NFR-SC-003: Email Credentials
- **Status**: ⚠️ Hardcoded in `web/app.py`
- **Recommendation**: Move to environment variables

---

### 3.3 Reliability

#### NFR-RL-001: AI Connection Handling
- **Requirement**: Graceful degradation when Ollama unavailable
- **Status**: ✅ Implemented via `ollama_utils.safe_ollama_chat()`
- **Fallback**: Template responses, error messages

#### NFR-RL-002: Database Backups
- **Requirement**: Regular backups of `partnerai.db`
- **Status**: ❌ Not implemented
- **Recommendation**: Add automated backup script

#### NFR-RL-003: Error Logging
- **Status**: ⚠️ Basic print statements
- **Recommendation**: Implement proper logging framework (e.g., Python logging)

---

### 3.4 Scalability

#### NFR-SL-001: Database Choice
- **Current**: SQLite
- **Limitation**: Single-writer constraint
- **Recommendation**: Migrate to PostgreSQL for multi-user scaling

#### NFR-SL-002: AI Model Hosting
- **Current**: Local Ollama instance
- **Limitation**: Single-machine, GPU-dependent
- **Recommendation**: Consider cloud AI APIs for scaling

---

### 3.5 Usability

#### NFR-US-001: Mobile Responsiveness
- **Status**: ✅ Mobile-first design
- **Implementation**: Responsive CSS in templates

#### NFR-US-002: Accessibility
- **Status**: ⚠️ Basic HTML semantics
- **Recommendation**: Add ARIA labels, keyboard navigation

#### NFR-US-003: Internationalization
- **Status**: ❌ English-only
- **Future**: Support for multiple languages

---

## 4. Technical Requirements

### 4.1 Technology Stack

#### Backend
- **Framework**: Flask (Python 3.9+)
- **AI Engine**: Ollama (Local LLM)
- **Models**: Phi3, Mistral 7B
- **Database**: SQLite
- **Bot Framework**: python-telegram-bot

#### Frontend
- **HTML/CSS**: Vanilla (No framework)
- **JavaScript**: Vanilla ES6
- **Typography**: Inter, Poppins (Google Fonts)
- **Color Scheme**: Purple-themed

#### Dependencies
```
flask
ollama
python-telegram-bot
requests
```

---

### 4.2 System Architecture

#### Components
1. **Web Server** (`web/app.py`) - Flask routes and API endpoints
2. **Telegram Bot** (`partnerai.py`) - Telegram interface
3. **AI Layer** (`ollama_utils.py`) - Ollama integration
4. **Data Layer** (`memory.py`) - Database operations
5. **Intelligence Engines**:
   - Habit Intelligence (`habit_intelligence.py`)
   - Smart Blocks (`smart_blocks.py`, `smart_blocks_db.py`)
   - Coach Engine (`coach_engine.py`)

#### Database Schema
- **users**: User profiles and authentication
- **chat_history**: 1-on-1 chat messages
- **group_chat_messages**: Team chat messages
- **groups**: Team/group metadata
- **group_members**: Group membership
- **group_tasks**: Task assignments
- **daily_tasks**: Daily to-do items
- **smart_blocks**: Knowledge blocks
- **block_relationships**: Block connections
- **habit_analytics**: Habit completion data
- **user_rewards**: Gamification rewards
- **weekly_reports**: Coaching reports
- **focus_sessions**: Productivity sessions
- **daily_articles**: Generated articles
- **daily_news**: Curated news
- **community_posts**: Social posts

---

### 4.3 AI Model Configuration

#### Model Selection
- **Main Model**: Phi3 (Lightweight, efficient)
- **Group Model**: Phi3
- **Fallback**: Mistral 7B

#### System Prompts
- **Location**: [`mentor_prompt.py`](file:///c:/Users/yo405/PartnerAI/mentor_prompt.py)
- **Personality**: Calm, reliable, human-like AI companion
- **Style**: Structured responses with emojis, bullet points

---

## 5. Development Priorities

### Phase 1: Critical Issues (Immediate)
1. ⚠️ **Security**: Implement password hashing
2. ⚠️ **Security**: Move email credentials to environment variables
3. ⚠️ **Reliability**: Add proper error logging

### Phase 2: Core Enhancements (Short-term)
4. ✨ **Feature**: Complete Smart Blocks UI integration
5. ✨ **Feature**: Enhanced habit analytics dashboard
6. ✨ **UX**: Improved mobile experience

### Phase 3: Scaling (Mid-term)
7. 🚀 **Infrastructure**: Migrate to PostgreSQL
8. 🚀 **Infrastructure**: Implement backup system
9. 🚀 **Performance**: Optimize AI response caching

### Phase 4: Future Enhancements (Long-term)
10. 🌟 **AI**: Multi-model support (GPT-4, Claude)
11. 🌟 **Social**: Enhanced community features
12. 🌟 **Mobile**: Native mobile apps (iOS/Android)

---

## 6. Acceptance Criteria

### For Each Feature
- [ ] Unit tests pass (where applicable)
- [ ] Manual testing completed
- [ ] Documentation updated
- [ ] Security review passed
- [ ] Performance benchmarks met
- [ ] User feedback collected

---

## 7. Glossary

| Term | Definition |
|------|------------|
| **Smart Block** | Modular knowledge unit (idea, task, learning, habit, reflection) |
| **Habit Intelligence** | AI system for analyzing habit patterns and suggesting improvements |
| **Coach Engine** | AI-powered weekly analysis and strategic recommendations |
| **Focus Session** | Timed productivity session with optional music/wallpaper |
| **Mentor AI** | AI persona in group chats (user_id: 0) |
| **Streak** | Consecutive days of task completion |
| **Progress Score** | 0-100 metric calculated from habits, tasks, and engagement |

---

## Document Version
- **Version**: 1.0
- **Date**: 2026-01-21
- **Status**: Living Document

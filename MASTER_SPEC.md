# 1. Executive Summary

## RewardsPilotOS

**Version:** 1.0 (Draft)

**Author:** Tanisha Garg

**Status:** Product Discovery

---

## One-Line Description

**RewardsPilotOS is an AI-powered credit card rewards decision engine that continuously helps users maximize the lifetime value of every credit card they own by optimizing spending, benefits, transfers, and redemptions across multiple reward ecosystems.**

---

## Vision

Modern credit card ecosystems have evolved into complex financial products rather than simple payment instruments.

A single premium card may include:

- Reward points
- Milestone benefits
- Merchant offers
- Lounge access
- Travel insurance
- Dining privileges
- Airline transfer partners
- Hotel transfer partners
- Accelerated earning categories
- Monthly reward caps
- Promotional campaigns

Users increasingly own multiple premium cards, creating a portfolio management problem rather than a single-card optimization problem.

As this complexity grows, users spend significant time researching blogs, community forums, spreadsheets, and official documentation to answer questions such as:

- Which card should I use today?
- Should I buy a SmartBuy voucher?
- Have I exhausted my accelerated reward cap?
- Should I transfer points now or wait?
- Which airline offers the highest redemption value?
- Which hotel program provides the greatest overall return?
- Is it worth paying the annual fee this year?

RewardsPilotOS aims to solve these problems through a continuously learning AI system that acts as a personal rewards strategist.

---

## Why This Project Exists

Existing products generally solve isolated problems.

Examples include:

- Card comparison websites
- Cashback calculators
- Award flight search tools
- Reward point calculators
- Community forums
- Travel blogs

Each provides valuable information but requires users to manually combine multiple sources before making a decision.

The result is:

- Fragmented information
- Outdated advice
- Inconsistent recommendations
- High research effort
- Irreversible mistakes

RewardsPilotOS shifts the experience from **manual research** to **AI-assisted decision making**.

---

## Problem Statement

The current rewards ecosystem suffers from five fundamental problems.

### 1. Information Fragmentation

Reward rules are distributed across:

- Bank websites
- PDFs
- SmartBuy portals
- Airline loyalty programs
- Hotel loyalty programs
- Blogs
- Community forums

No single source maintains an up-to-date, integrated view.

---

### 2. Constantly Changing Rules

Reward ecosystems evolve frequently.

Examples include:

- SmartBuy earning caps
- Transfer bonuses
- Partner additions
- Partner removals
- Redemption devaluations
- Milestone revisions

Static calculators become outdated quickly.

---

### 3. Portfolio Complexity

Users increasingly own multiple premium cards.

Each card introduces:

- Different reward currencies
- Earning structures
- Transfer partners
- Redemption strengths
- Limitations

Optimizing across multiple cards becomes exponentially harder than optimizing a single card.

---

### 4. Irreversible Decisions

Many reward transfers cannot be reversed.

Poor decisions may permanently reduce redemption value.

Users therefore require trustworthy recommendations supported by transparent reasoning.

---

### 5. Time Cost

Experienced reward enthusiasts often spend hours researching before making high-value redemptions.

The research itself has become a significant cost.

---

## North Star

> **Help users maximize the lifetime value of every credit card they own. RewardsPilotOS is an AI-powered decision intelligence platform that helps users make the best rewards decision at every stage of the credit card lifecycle.**

Everything within RewardsPilotOS should support this objective.

---

## Product Philosophy

The product is designed around the following principles.

### Optimize the portfolio, not individual transactions.

Recommendations should maximize long-term value instead of immediate gains.

### Build trust before automation.

Every recommendation should include:

- Supporting evidence
- Confidence score
- Source citations
- Freshness timestamp

### Personalization is mandatory.

Recommendations should adapt based on:

- Travel preferences
- Spending behavior
- Redemption history
- Previous decisions
- Stated goals

### AI augments human decision making.

RewardsPilotOS assists users in making better decisions.

It never performs financial actions automatically.

---

## Product Scope

### MVP

Supported issuers:

- HDFC
- Axis
- American Express

Core functionality:

- Spend optimization
- SmartBuy optimization
- Reward cap tracking
- Transfer partner optimization
- Airline redemption
- Hotel redemption
- Personalized recommendations

User balances will be entered manually.

---

### Future Scope

Additional issuers:

- HSBC
- ICICI
- SBI

Additional capabilities:

- Lounge optimization
- Annual fee recommendations
- Statement parsing
- Milestone prediction
- Point expiry forecasting
- Transfer bonus alerts
- Benefit utilization analytics

---

## Success Criteria

The project succeeds if it demonstrates:

### Product Thinking

- Clear problem definition
- Strong user validation
- Thoughtful prioritization

### AI Architecture

Appropriate use of:

- Multi-agent orchestration
- Hybrid Retrieval
- Graph optimization
- Structured rule reasoning
- Long-term memory

### Engineering

- Modular architecture
- Production-quality implementation
- Scalable design
- Clear documentation

### Portfolio Value

A recruiter should immediately understand:

- The customer problem
- The product strategy
- The architectural decisions
- Why every AI component exists

---

## Why This Project Was Chosen

Several portfolio ideas were explored, including ForexFlow and IntentShelf.

RewardsPilotOS was selected because it satisfies four key criteria:

1. It solves a genuine decision-making problem for a clearly defined user segment.
2. The problem naturally justifies AI techniques such as Hybrid Retrieval, graph optimization, memory, and multi-agent orchestration.
3. The product can be built using publicly available data without requiring proprietary integrations.
4. It demonstrates end-to-end AI product development, from customer discovery to deployment and evaluation.

---

## Purpose of This Document

This document is the canonical specification for RewardsPilotOS.

It serves as the single source of truth for:

- Product strategy
- AI architecture
- Engineering design
- Coding agents
- Documentation
- Repository generation

All implementation decisions should trace back to this specification.

---

# 2. Why RewardsPilotOS?

## Motivation

RewardsPilotOS was conceived as a flagship AI Product Management portfolio project to demonstrate the design and implementation of a production-grade AI system that solves a real-world decision-making problem.

The objective is not to build another rewards calculator. The objective is to design an intelligent decision engine that combines AI reasoning, structured knowledge, graph optimization, and persistent user memory to provide personalized recommendations.

This project showcases end-to-end product thinking, including customer discovery, product strategy, AI system design, software architecture, evaluation, and deployment.

---

## Why This Problem?

Premium credit card adoption is growing rapidly, especially in India.

Users increasingly hold multiple cards such as:

- HDFC Infinia
- Axis Atlas
- American Express Platinum Travel
- HSBC Premier
- ICICI Emeralde
- SBI Aurum

Each card offers different:

- Reward currencies
- Merchant multipliers
- Accelerated earning programs
- Transfer partners
- Reward caps
- Lounge benefits
- Milestone benefits
- Promotional campaigns

As users acquire more cards, optimizing rewards becomes increasingly difficult.

---

## Current User Experience

A user planning a purchase or trip typically performs several manual steps.

1. Search blogs and Reddit.
2. Compare reward rates across cards.
3. Check SmartBuy eligibility.
4. Verify monthly reward caps.
5. Look for transfer bonuses.
6. Compare airline and hotel transfer partners.
7. Estimate redemption value.
8. Make a manual decision.

This process is slow, fragmented, and error-prone.

---

## Core Pain Points

### Information Fragmentation

Reward rules are scattered across bank websites, loyalty programs, blogs, PDFs, and community forums.

---

### Dynamic Rules

Banks frequently change:

- Reward rates
- SmartBuy caps
- Transfer ratios
- Promotions
- Redemption rules

Static calculators quickly become outdated.

---

### Multi-Card Optimization

Most users optimize one card at a time.

The real problem is optimizing an entire portfolio of cards over months or years.

---

### Irreversible Decisions

Many reward transfers cannot be reversed.

Poor decisions permanently reduce value.

---

### Research Overhead

Enthusiasts spend significant time researching before making purchases or redemptions.

The effort often outweighs the value gained.

---

## Why Existing Solutions Fall Short

Most existing tools focus on a single problem.

Examples include:

- Card comparison websites
- Reward calculators
- Award search engines
- Travel blogs
- Bank portals

None provide continuous portfolio-level optimization.

Users are still responsible for combining information from multiple sources before making decisions.

---

## Opportunity

Advances in LLMs, retrieval systems, and agent orchestration enable a new category of products.

Instead of helping users search for information, RewardsPilotOS helps users make better decisions.

The product acts as an intelligent copilot that understands:

- The user's portfolio
- Current reward rules
- Historical preferences
- Travel goals
- Spending patterns
- Available transfer options

It then recommends the optimal action with supporting evidence.

---

## Why AI Is Justified

Artificial intelligence is not included for novelty.

Each AI capability solves a specific product problem.

| Capability | Problem Solved |
|------------|----------------|
| Multi-Agent System | Breaks complex planning into specialized reasoning tasks |
| Hybrid Retrieval | Retrieves current reward rules and documentation |
| Graph Optimization | Finds the best transfer and redemption path |
| Long-Term Memory | Learns user preferences and history |
| Rule Engine | Applies deterministic issuer policies |
| LLM | Explains recommendations and handles natural language interaction |

---

## Why This Is A Strong Portfolio Project

The project demonstrates multiple dimensions of AI Product Management.

### Product

- Customer discovery
- Product strategy
- Feature prioritization
- Roadmap planning

### AI

- Multi-agent orchestration
- Hybrid Retrieval
- Knowledge pipelines
- Memory architecture

### Engineering

- Modular backend
- Modern frontend
- Graph algorithms
- Scalable architecture

### Evaluation

- AI evaluation metrics
- Product KPIs
- Recommendation quality
- Retrieval quality

---

## Project Goals

The project aims to demonstrate:

- Strong product thinking
- Practical AI system design
- Production-grade software architecture
- Explainable recommendations
- Measurable evaluation
- High-quality engineering documentation

---

## Non Goals

The MVP will not:

- Connect directly to bank accounts
- Execute financial transactions
- Book travel automatically
- Recommend financial investments
- Replace official banking applications

The system remains an intelligent decision-support platform.

---

# 3. Problem Discovery

## Objective

Understand the current state of credit card rewards management, identify unmet user needs, validate the problem space, and define the opportunity for RewardsPilotOS.

---

# Industry Background

Credit card reward ecosystems have evolved from simple cashback programs into complex loyalty platforms.

A premium credit card now includes multiple reward mechanisms, including:

- Base reward points
- Accelerated reward categories
- Merchant-specific offers
- Milestone rewards
- Lounge access
- Travel benefits
- Hotel partnerships
- Airline transfer partners
- Limited-time promotions
- Annual renewal benefits

Users increasingly own multiple premium cards, making optimization significantly more difficult.

The challenge is no longer choosing the best card. It is managing an entire rewards portfolio.

---

# Existing User Workflow

A typical user planning a high-value purchase or trip follows a fragmented workflow.

1. Decide what they want to purchase or where they want to travel.
2. Compare earning rates across multiple cards.
3. Check merchant-specific offers.
4. Verify SmartBuy eligibility.
5. Check monthly reward caps.
6. Compare airline transfer partners.
7. Compare hotel transfer partners.
8. Search Reddit and travel blogs.
9. Calculate redemption value manually.
10. Make a decision.

This process often takes between 30 minutes and several hours.

---

# User Pain Points

## Fragmented Information

Reward rules are spread across:

- Bank websites
- PDFs
- SmartBuy
- Airline loyalty programs
- Hotel loyalty programs
- Community forums
- Travel blogs

Users must manually combine information from multiple sources.

---

## Constantly Changing Rules

Reward programs change frequently.

Examples include:

- SmartBuy reward caps
- Transfer bonuses
- Transfer ratios
- Partner additions
- Redemption devaluations
- Benefit revisions

Users struggle to stay current.

---

## Portfolio Complexity

Each card has different:

- Reward currencies
- Multipliers
- Spending categories
- Transfer partners
- Redemption strengths
- Benefit caps

Optimizing multiple cards simultaneously becomes increasingly complex.

---

## Irreversible Decisions

Many point transfers cannot be reversed.

Poor decisions permanently reduce value.

Users seek confidence before transferring points.

---

## Time Intensive Research

Enthusiasts spend considerable time researching before making purchases or bookings.

Research itself becomes a hidden cost.

---

# Jobs To Be Done

## Functional Jobs

- Help me choose the best card for every purchase.
- Help me maximize reward earnings.
- Help me plan travel redemptions.
- Help me avoid wasting points.
- Help me track reward caps.
- Help me identify transfer opportunities.

---

## Emotional Jobs

- Reduce uncertainty.
- Increase confidence.
- Avoid regret.
- Feel in control of my rewards.

---

## Social Jobs

- Demonstrate expertise within rewards communities.
- Share optimized redemption strategies.

---

# Assumptions

The following assumptions will be validated during user research.

### Assumption 1

Users holding multiple premium cards struggle to remember changing reward rules.

---

### Assumption 2

Users trust recommendations when supported by official documentation.

---

### Assumption 3

Users prefer personalized recommendations over generic calculators.

---

### Assumption 4

Users are willing to manually maintain reward balances if recommendation quality improves.

---

### Assumption 5

Users value explainability more than complete automation.

---

# Problem Statements

### Problem Statement 1

Users struggle to determine which credit card provides the highest overall value for a given purchase.

---

### Problem Statement 2

Users struggle to track frequently changing reward rules across multiple issuers.

---

### Problem Statement 3

Users struggle to identify the optimal transfer and redemption strategy for long-term value.

---

### Problem Statement 4

Users spend excessive time researching instead of making informed decisions.

---

# Opportunity Statement

Build an AI-powered credit card rewards decision engine that continuously understands the user's portfolio, retrieves the latest reward rules, reasons across reward ecosystems, and recommends the optimal earning, benefit utilization, transfer, and redemption strategy with transparent, evidence-backed explanations.

---

# Why This Problem Is Suitable For AI

The problem combines deterministic rules with probabilistic reasoning.

Some decisions require exact calculations.

Examples:

- Reward multipliers
- Transfer ratios
- Monthly caps

Other decisions require contextual reasoning.

Examples:

- Future travel goals
- Preferred airlines
- Hotel preferences
- Timing of transfers

The combination of structured reasoning and natural language interaction makes this a strong candidate for a hybrid AI system.

---

# Success Criteria

The problem is considered solved if users can:

- Decide which card to use within seconds.
- Understand why a recommendation was made.
- Trust the recommendation.
- Spend less time researching.
- Achieve greater long-term rewards value.

---

# Open Questions

These questions will guide future user research.

- How many premium cards does the average target user own?
- How often do users actively redeem points?
- Which reward ecosystems create the most confusion?
- Which benefits are underutilized?
- What information do users trust most?
- Which recommendations would users be unwilling to delegate to AI?

---

# 4. Competitor Analysis

## Objective

Understand the current competitive landscape, identify market gaps, and define the unique positioning of RewardsPilotOS.

---

# Market Overview

The rewards ecosystem is fragmented.

Existing products generally focus on one part of the rewards lifecycle rather than optimizing the complete user journey.

Broadly, the market can be divided into the following categories:

- Bank applications
- Credit card comparison websites
- Reward calculators
- Award search platforms
- Travel blogs
- Community forums
- Spreadsheet-based personal trackers

No single platform combines portfolio management, AI reasoning, retrieval, graph optimization, and personalized recommendations.

---

# Competitive Landscape

| Category | Examples | Primary Purpose |
|----------|----------|-----------------|
| Bank Apps | HDFC SmartBuy, Axis Mobile, Amex India | Manage issuer-specific rewards |
| Award Search | Point.me, Seats.aero | Find award flight availability |
| Card Comparison | CardMaven, TechnoFino, CardInsider | Compare cards and benefits |
| Tracking | AwardWallet | Track loyalty balances |
| Community | Reddit, FlyerTalk, Team-BHP | User discussions and advice |
| Manual | Excel, Notion | Personal reward tracking |

---

# Competitor Analysis

## HDFC SmartBuy

### Strengths

- Official source
- Voucher marketplace
- Accelerated reward earnings
- Travel booking integration

### Weaknesses

- Limited to HDFC ecosystem
- No portfolio optimization
- No personalization
- No cross-bank recommendations

---

## AwardWallet

### Strengths

- Loyalty balance tracking
- Expiry monitoring
- Wide program coverage

### Weaknesses

- Minimal decision support
- Limited optimization
- No spend recommendations
- No graph reasoning

---

## Point.me

### Strengths

- Excellent award redemption search
- Airline coverage
- Transfer guidance

### Weaknesses

- Travel-focused
- No spend optimization
- No Indian ecosystem
- No card portfolio intelligence

---

## Card Comparison Websites

Examples:

- CardMaven
- TechnoFino
- CardInsider

### Strengths

- Rich educational content
- Benefit explanations
- Card comparisons

### Weaknesses

- Static information
- No personalization
- No optimization engine
- No memory

---

## Community Forums

Examples

- Reddit
- FlyerTalk
- Team-BHP

### Strengths

- Real user experiences
- Timely discussions
- Hidden optimization strategies

### Weaknesses

- Information overload
- Inconsistent quality
- Difficult to verify
- Requires manual research

---

# Competitive Feature Comparison

| Capability | Bank Apps | AwardWallet | Point.me | Blogs | RewardsPilotOS |
|------------|-----------|-------------|----------|-------|----------------|
| Multi-card optimization | ❌ | ❌ | ❌ | ❌ | ✅ |
| Personalized recommendations | ❌ | Limited | Limited | ❌ | ✅ |
| AI assistant | ❌ | ❌ | Limited | ❌ | ✅ |
| Hybrid Retrieval | ❌ | ❌ | ❌ | ❌ | ✅ |
| Multi-agent reasoning | ❌ | ❌ | ❌ | ❌ | ✅ |
| Graph optimization | ❌ | ❌ | ❌ | ❌ | ✅ |
| Long-term memory | ❌ | Limited | ❌ | ❌ | ✅ |
| Explainable recommendations | Limited | ❌ | Limited | ❌ | ✅ |
| Cross-bank optimization | ❌ | ❌ | ❌ | ❌ | ✅ |
| SmartBuy optimization | Limited | ❌ | ❌ | Partial | ✅ |

---

# Market Gap

Current products answer questions such as:

- What benefits does this card provide?
- How many points do I have?
- Which flights are available?

Users still answer the most important question themselves:

> **"What should I do next?"**

RewardsPilotOS focuses on answering this question.

---

# Product Positioning

RewardsPilotOS is positioned as an **AI Decision Engine for Credit Card Rewards**.

Rather than functioning as a calculator or database, it continuously evaluates the user's portfolio and recommends the next best action.

Examples include:

- Use Card A instead of Card B.
- Buy vouchers through SmartBuy this month.
- Delay transferring points until a promotion begins.
- Redeem through Marriott instead of KrisFlyer.
- Stop using SmartBuy because your reward cap has been reached.
- Shift spending to another card to unlock a milestone.

---

# Key Differentiators

## Portfolio-Level Optimization

The system optimizes an entire portfolio instead of individual transactions.

---

## Personalized Intelligence

Recommendations consider:

- User balances
- Spending habits
- Travel goals
- Preferred airlines
- Preferred hotels
- Historical decisions

---

## Hybrid AI Architecture

The product combines:

- Structured rule engine
- Hybrid Retrieval
- Knowledge graph
- Long-term memory
- Multi-agent orchestration

Each component exists because it solves a specific problem.

---

## Explainability

Every recommendation includes:

- Reasoning
- Source citations
- Rule references
- Confidence score
- Last verified timestamp

---

## India-First Design

The MVP is designed around Indian premium credit card users, including:

- HDFC
- Axis
- American Express

Future versions will expand to additional issuers.

---

# SWOT Analysis

## Strengths

- Strong AI architecture
- Clear differentiation
- Explainable recommendations
- Personalized planning
- Portfolio optimization

## Weaknesses

- Knowledge base requires continuous maintenance
- Manual balance updates in MVP
- Dependent on public information

## Opportunities

- Growing premium card adoption
- Increasing rewards complexity
- AI-native financial assistants
- Enterprise partnerships
- Global expansion

## Threats

- Banks changing APIs or policies
- Rapid rule changes
- New competitors
- Regulatory changes
- Hallucination risks if retrieval fails

---

# Why This Project Is Worth Building

The opportunity is not to build another rewards calculator.

The opportunity is to build an intelligent decision-support platform that transforms fragmented reward information into actionable, personalized recommendations.

RewardsPilotOS aims to become the AI decision engine that helps users maximize the lifetime value of every credit card they own.

---

# 5. User Research

## Objective

Understand the behaviors, motivations, pain points, and decision-making process of users who actively optimize credit card rewards to validate the need for RewardsPilotOS.

---

# Research Goals

The research aims to answer the following questions:

- How do users currently manage multiple credit cards?
- How much time do users spend researching rewards?
- Which decisions are the most difficult?
- What sources of information do users trust?
- Which benefits are underutilized?
- Would users trust AI-generated recommendations?
- What level of personalization do users expect?

---

# Target Participants

The primary audience consists of users who actively optimize rewards rather than casual credit card holders.

### Segment 1

Premium credit card enthusiasts.

Examples:

- HDFC Infinia
- Axis Atlas
- American Express Platinum Travel

---

### Segment 2

Frequent travelers.

Characteristics:

- Multiple international trips per year
- Airline loyalty memberships
- Hotel loyalty memberships
- High annual spend

---

### Segment 3

Reward beginners.

Characteristics:

- Recently acquired first premium card
- Interested in maximizing benefits
- Limited knowledge of reward ecosystems

---

# Research Methodology

The following methods will be used.

### User Interviews

Conduct semi-structured interviews with premium card holders.

Objective:

Understand current workflows and frustrations.

---

### Community Research

Analyze discussions across:

- Reddit
- Team-BHP
- FlyerTalk
- TechnoFino

Objective:

Identify recurring questions and emerging pain points.

---

### Competitive Analysis

Study existing products to understand:

- User workflows
- Missing capabilities
- Common complaints

---

### Secondary Research

Review:

- Bank documentation
- Reward program guides
- Travel blogs
- Loyalty program documentation

---

# Research Questions

## Card Usage

- How many premium cards do you currently own?
- Which card do you use most frequently?
- How do you decide which card to use?

---

## Reward Management

- How do you currently track reward balances?
- How often do you redeem points?
- Which reward programs do you value most?

---

## Travel Planning

- How do you decide when to transfer points?
- Which airline and hotel programs do you use?
- What is the most confusing part of redemption planning?

---

## Information Sources

- Which websites do you trust?
- How often do you search Reddit?
- Which blogs do you follow?

---

## AI

- Would you trust an AI recommendation?
- What evidence would increase your confidence?
- Would you prefer recommendations or full automation?

---

# Key Research Hypotheses

## H1

Users holding multiple premium cards struggle to remember changing reward rules.

---

## H2

Users spend excessive time researching before making high-value purchases or redemptions.

---

## H3

Users trust recommendations backed by official documentation more than generic AI responses.

---

## H4

Users value explainability more than automation.

---

## H5

Users prefer proactive recommendations over manually searching for information.

---

# Expected Insights

The research is expected to validate that users need:

- Portfolio-level optimization
- Personalized recommendations
- Faster decision making
- Transparent reasoning
- Continuous monitoring of changing reward rules

---

# Success Criteria

The research will be considered successful if it confirms:

- A measurable decision-making problem exists.
- Existing tools fail to solve the problem end-to-end.
- Users are willing to use an AI assistant for reward optimization.
- Personalized recommendations provide meaningful value over static calculators.

---

# Research Deliverables

The outcome of this research will produce:

- User personas
- Journey maps
- Jobs To Be Done
- Prioritized pain points
- Product requirements
- Feature prioritization

---

# 6. User Personas

## Objective

Define the primary user segments for RewardsPilotOS to ensure product decisions, feature prioritization, and AI recommendations are designed around real user needs.

---

# Persona 1: The Rewards Enthusiast

## Profile

**Name:** Rahul Sharma

**Age:** 32

**Occupation:** Software Engineer

**Location:** Bengaluru

**Annual Income:** ₹40L+

**Cards**

- HDFC Infinia
- Axis Atlas
- Amex Platinum Travel

---

## Goals

- Maximize reward earnings.
- Travel in Business Class using points.
- Earn enough hotel points for luxury stays.
- Avoid wasting transferable points.

---

## Behaviors

- Reads TechnoFino and Reddit regularly.
- Tracks promotions manually.
- Maintains Excel spreadsheets.
- Plans redemptions months in advance.

---

## Pain Points

- Rules change frequently.
- SmartBuy limits are confusing.
- Unsure when to transfer points.
- Difficult to compare multiple transfer partners.
- Time-consuming research.

---

## Current Workflow

1. Search Reddit.
2. Read blogs.
3. Compare transfer partners.
4. Calculate redemption value.
5. Make a manual decision.

---

## AI Expectations

- Personalized recommendations.
- Latest reward rules.
- Source citations.
- Transparent reasoning.

---

## Success for Rahul

"I spend less time researching while getting better redemption value."

---

# Persona 2: The Frequent Business Traveler

## Profile

**Name:** Priya Mehta

**Age:** 38

**Occupation:** Product Director

**Location:** Mumbai

**Annual Income:** ₹70L+

**Cards**

- HDFC Infinia
- HSBC Premier
- Amex Platinum Charge

---

## Goals

- Reduce travel expenses.
- Use premium benefits.
- Never miss lounge or hotel benefits.
- Track annual milestones.

---

## Behaviors

- Travels internationally every month.
- Uses Marriott and Accor frequently.
- Doesn't actively follow rewards communities.

---

## Pain Points

- Doesn't have time to research.
- Often forgets available benefits.
- Unsure whether annual fees remain worthwhile.

---

## AI Expectations

- Proactive alerts.
- Simple recommendations.
- Minimal manual effort.

---

## Success for Priya

"I never miss valuable benefits without spending hours researching."

---

# Persona 3: The Premium Card Beginner

## Profile

**Name:** Arjun Verma

**Age:** 28

**Occupation:** Consultant

**Location:** Gurgaon

**Annual Income:** ₹22L+

**Cards**

- HDFC Regalia Gold
- Amex Membership Rewards Credit Card

---

## Goals

- Learn how rewards work.
- Maximize value.
- Avoid beginner mistakes.

---

## Behaviors

- Watches YouTube videos.
- Reads comparison blogs.
- Searches Google before purchases.

---

## Pain Points

- Doesn't understand transfer partners.
- Confused by reward terminology.
- Doesn't know which card to use.

---

## AI Expectations

- Educational explanations.
- Beginner-friendly guidance.
- Easy-to-understand recommendations.

---

## Success for Arjun

"I feel confident making rewards decisions without becoming an expert."

---

# Common Themes

Across all personas, several needs consistently emerge.

## Shared Goals

- Maximize reward value.
- Save time.
- Reduce decision fatigue.
- Avoid costly mistakes.
- Trust recommendations.

---

## Shared Pain Points

- Fragmented information.
- Constant rule changes.
- Portfolio complexity.
- Manual calculations.
- Lack of personalized guidance.

---

## Design Implications

These personas shape several core product decisions.

- Recommendations must be personalized.
- Every recommendation should include an explanation.
- The system must monitor changing rules continuously.
- The product should optimize the entire rewards portfolio rather than individual transactions.
- AI should assist decision making without removing user control.

---

# 7. Jobs To Be Done (JTBD)

## Objective

Identify the core jobs users are trying to accomplish when managing credit card rewards. These jobs drive product decisions, feature prioritization, and AI system design.

---

# Primary Job

> Help me maximize the lifetime value of every credit card I own with minimal effort and confidence in every decision.

This is the core job that RewardsPilotOS aims to solve.

---

# Functional Jobs

## Earn Rewards Efficiently

Users want to:

- Choose the best card for every purchase.
- Maximize reward earnings.
- Unlock spending milestones.
- Utilize merchant-specific offers.
- Avoid exceeding monthly reward caps.

Current solution:

- Manual calculations
- Blogs
- Excel sheets

Desired outcome:

"I always know which card gives me the highest value."

---

## Manage Rewards Portfolio

Users want to:

- Track reward balances.
- Track milestone progress.
- Track benefit utilization.
- Track reward expiry.
- View their entire portfolio in one place.

Current solution:

- Multiple banking apps
- Loyalty program websites
- Manual tracking

Desired outcome:

"I understand my entire rewards portfolio at a glance."

---

## Optimize Point Transfers

Users want to:

- Compare airline partners.
- Compare hotel partners.
- Identify transfer bonuses.
- Choose the best transfer path.

Current solution:

- Reddit
- TechnoFino
- Travel blogs

Desired outcome:

"I transfer points only when it maximizes long-term value."

---

## Optimize Redemptions

Users want to:

- Maximize value per point.
- Book premium travel.
- Compare multiple redemption options.
- Avoid poor-value redemptions.

Desired outcome:

"I always redeem my points intelligently."

---

## Utilize Card Benefits

Users want to:

- Use lounge access.
- Use hotel privileges.
- Use dining offers.
- Use merchant discounts.
- Use travel insurance.

Desired outcome:

"I never miss benefits that I'm already paying for."

---

# Emotional Jobs

Users want to feel:

- Confident.
- In control.
- Informed.
- Smart.
- Efficient.

They do not want to feel:

- Confused.
- Overwhelmed.
- Regret after transferring points.
- Fear of missing a better redemption.

---

# Social Jobs

Users often want to:

- Share successful redemption strategies.
- Demonstrate expertise.
- Help friends choose better cards.
- Participate in rewards communities.

---

# Trigger Events

Users typically seek help during specific moments.

Examples include:

- Booking an international trip.
- Purchasing electronics.
- Paying annual insurance premiums.
- Buying SmartBuy vouchers.
- Annual fee renewal.
- Point expiry.
- Transfer bonus announcements.
- Launch of a new credit card.

These moments represent high-value engagement opportunities.

---

# Current Alternatives

Today, users rely on:

- Bank applications
- SmartBuy
- TechnoFino
- CardMaven
- Reddit
- FlyerTalk
- YouTube
- Excel
- Google Search

Users manually combine information from these sources before making decisions.

---

# Desired Outcomes

Users want to:

- Spend less time researching.
- Earn more rewards.
- Make better redemption decisions.
- Never miss valuable benefits.
- Trust every recommendation.

---

# Mapping Jobs to Product Features

| User Job | RewardsPilotOS Feature |
|-----------|------------------------|
| Choose the best card | Spend Optimization Engine |
| Maximize reward earnings | Rule Engine + Recommendation Engine |
| Track reward balances | Portfolio Dashboard |
| Monitor reward caps | Rule Engine + Notifications |
| Compare transfer partners | Graph Optimization Engine |
| Plan travel redemptions | AI Planner Agent |
| Track benefits | Benefit Tracker |
| Learn reward rules | Hybrid Retrieval + Explainable AI |
| Stay updated | Knowledge Pipeline + Notification Agent |

---

# Product Insight

Users are not looking for another rewards calculator.

They are looking for an intelligent system that answers a single question throughout the lifecycle of their credit cards:

> **"Given my cards, my goals, and the current reward ecosystem, what should I do next?"**

Everything in RewardsPilotOS should ultimately answer this question.

---

# 8. Opportunity Analysis & Product Strategy

## Objective

Evaluate the market opportunity, justify why RewardsPilotOS should exist, and define the product strategy, positioning, and long-term vision.

---

# Market Opportunity

The premium credit card market is growing rapidly, with users increasingly holding multiple rewards-focused cards across different issuers.

Each issuer introduces unique reward currencies, transfer partners, benefit structures, promotional campaigns, and redemption rules.

As the number of cards increases, users face an increasingly complex optimization problem.

The opportunity is no longer helping users understand individual cards.

The opportunity is helping users optimize an entire portfolio.

---

# Why Now?

Several trends make this the right time to build RewardsPilotOS.

## Increasing Product Complexity

Premium credit cards continue to introduce:

- Dynamic reward multipliers
- Merchant partnerships
- Milestone rewards
- Monthly earning caps
- Transfer bonuses
- Limited-time promotions

Managing these changes manually has become increasingly difficult.

---

## Growth of AI Decision Support

Modern LLMs can combine reasoning, retrieval, structured rules, and personalized memory to solve complex decision-making problems.

Instead of simply answering questions, AI systems can recommend the optimal next action.

---

## Lack of Integrated Solutions

Current solutions are fragmented.

Users still combine multiple tools before making a decision.

No single platform provides:

- Portfolio optimization
- Personalized planning
- Continuous monitoring
- Explainable recommendations

---

# Why AI?

Artificial intelligence is included only where it provides clear value.

| Product Need | AI Capability |
|--------------|---------------|
| Understand user intent | LLM |
| Retrieve latest rules | Hybrid Retrieval |
| Plan across multiple steps | Multi-Agent System |
| Personalize recommendations | Long-Term Memory |
| Explain recommendations | LLM |
| Optimize transfer paths | Graph Algorithms |
| Apply issuer rules | Rule Engine |

Each AI component solves a specific product problem.

---

# Product Positioning

RewardsPilotOS is positioned as an:

> **AI-powered Credit Card Rewards Decision Engine**

Rather than acting as a database or calculator, the product continuously evaluates the user's rewards portfolio and recommends the next best action.

---

# Product Vision

Enable users to maximize the lifetime value of every credit card they own through intelligent, personalized, and explainable recommendations.

---

# Product Mission

Reduce the effort required to manage complex credit card reward ecosystems while increasing the value users receive from every purchase, benefit, transfer, and redemption.

---

# Product Principles

## Portfolio First

Optimize the complete portfolio rather than individual transactions.

---

## Explain Everything

Every recommendation must include:

- Supporting evidence
- Rule references
- Source citations
- Confidence score
- Last verified timestamp

---

## Personalization by Default

Recommendations should adapt to:

- Spending patterns
- Reward balances
- Travel goals
- Preferred airlines
- Preferred hotels
- Historical decisions

---

## Human in Control

The system recommends actions.

Users always make the final decision.

---

## Fresh Knowledge

Recommendations should be based on the latest available reward rules and program updates.

---

# Product Pillars

## Pillar 1

Spend Optimization

Help users earn rewards more efficiently.

---

## Pillar 2

Portfolio Intelligence

Provide complete visibility into rewards, milestones, and benefits.

---

## Pillar 3

Transfer Optimization

Recommend the highest-value transfer strategy.

---

## Pillar 4

Redemption Intelligence

Identify the best redemption opportunities.

---

## Pillar 5

Continuous Monitoring

Notify users when changing reward rules create better opportunities.

---

# MVP Strategy

The MVP focuses on solving one problem exceptionally well.

### Supported Issuers

- HDFC
- Axis
- American Express

### Supported Capabilities

- Spend optimization
- SmartBuy optimization
- Reward cap tracking
- Transfer optimization
- Hotel partners
- Airline partners
- Personalized recommendations

### Manual Inputs

- Reward balances
- Owned cards
- Travel goals
- Spending preferences

---

# Future Roadmap

Future releases may include:

- HSBC
- ICICI
- SBI
- Lounge tracking
- Statement parsing
- OCR
- Email parsing
- Automatic reward balance updates
- Predictive promotion alerts
- Award availability monitoring

---

# Why This Is A Strong AI Portfolio Project

RewardsPilotOS demonstrates the complete lifecycle of AI product development.

## Product

- Customer discovery
- Market analysis
- Product strategy
- Feature prioritization

## AI

- Multi-agent orchestration
- Hybrid Retrieval
- Knowledge pipeline
- Long-term memory
- Explainable AI

## Engineering

- Modern backend
- Scalable architecture
- Graph algorithms
- Production-ready APIs

## Evaluation

- Retrieval quality
- Recommendation quality
- Agent performance
- Product metrics

---

# Success Metrics

The product succeeds if users can:

- Make better rewards decisions.
- Spend less time researching.
- Increase realized reward value.
- Trust AI-generated recommendations.
- Return regularly to manage their rewards portfolio.
- Estimated Value Created (₹)

---

# Strategic Differentiation

Most products answer:

> "What rewards do I have?"

RewardsPilotOS answers:

> **"What should I do next, and why?"**

This shift from information retrieval to intelligent decision support defines the long-term strategy of the product.

---

# 9. Solution Overview

## Objective

Provide a high-level overview of RewardsPilotOS, explaining how the product works from the user's perspective and how the major system components work together to deliver personalized, explainable recommendations.

---

# What is RewardsPilotOS?

RewardsPilotOS is an AI-powered Credit Card Rewards Decision Engine that helps users maximize the lifetime value of every credit card they own.

Rather than acting as another rewards calculator, RewardsPilotOS continuously analyzes the user's credit card portfolio, reward balances, spending behavior, travel goals, and the latest reward program rules to recommend the optimal action.

The platform combines deterministic rule evaluation with AI reasoning to answer questions such as:

- Which card should I use for this purchase?
- Should I purchase vouchers through SmartBuy?
- Have I reached my monthly reward cap?
- Should I transfer points now or wait?
- Which airline offers the best redemption?
- Which hotel partner provides the highest value?
- Is my annual fee still worth paying?
- Am I missing valuable card benefits?

---

# Product Vision

Become the most trusted AI decision engine for credit card rewards by transforming fragmented reward information into personalized, evidence-backed recommendations.

---

# Core Product Philosophy

RewardsPilotOS is designed around five principles.

## Optimize the portfolio

Recommendations should maximize long-term portfolio value instead of optimizing individual transactions.

---

## Personalize every recommendation

Every user has different:

- Spending habits
- Travel goals
- Card portfolio
- Reward balances
- Risk tolerance
- Preferred airlines
- Preferred hotels

Recommendations should adapt accordingly.

---

## Explain every decision

Recommendations should never be black boxes.

Every recommendation should include:

- Supporting reasoning
- Source citations
- Relevant reward rules
- Confidence score
- Last verified timestamp

---

## Combine deterministic rules with AI reasoning

Some questions require exact calculations.

Examples include:

- Reward multipliers
- Transfer ratios
- Monthly caps
- Milestone progress

Other questions require contextual reasoning.

Examples include:

- Future travel plans
- Preferred redemption strategy
- Long-term optimization

RewardsPilotOS combines both approaches.

---

## Keep users in control

The platform recommends actions.

Users always decide what to do.

---

# Product Modules

The platform consists of several major modules.

## Portfolio Manager

Maintains:

- Owned cards
- Reward balances
- Loyalty memberships
- Spending preferences
- Travel goals

Acts as the user's profile.

---

## Knowledge Platform

Continuously collects information about:

- Card benefits
- Reward rules
- SmartBuy
- Transfer partners
- Promotions
- Airline programs
- Hotel programs

This becomes the product's knowledge base.

---

## Recommendation Engine

Generates personalized recommendations by combining:

- User context
- Current reward rules
- Portfolio state
- Transfer possibilities
- AI reasoning

---

## Transfer Optimization Engine

Builds a graph connecting:

- Credit cards
- Reward currencies
- Airline programs
- Hotel programs

Finds the highest-value redemption path.

---

## Rule Engine

Applies deterministic business logic such as:

- Reward calculations
- Monthly caps
- Spending milestones
- Eligibility checks

The Rule Engine guarantees correctness.

---

## AI Planning Engine

Handles questions requiring reasoning.

Examples include:

- Planning an international trip
- Optimizing points across multiple cards
- Timing transfers
- Comparing redemption strategies

---

## Notification Engine

Continuously monitors:

- Rule changes
- Promotions
- New transfer bonuses
- Reward expiry
- Benefit utilization

Notifies users when action is recommended.

---

# Example User Journey

Rahul owns:

- HDFC Infinia
- Axis Atlas
- Amex Platinum Travel

He wants to purchase a ₹90,000 laptop.

Instead of manually researching multiple websites, Rahul opens RewardsPilotOS.

He asks:

> "Which card should I use for this purchase?"

The system:

1. Understands Rahul's portfolio.
2. Retrieves current reward rules.
3. Checks SmartBuy eligibility.
4. Evaluates reward caps.
5. Calculates milestone progress.
6. Compares long-term reward value.
7. Generates the optimal recommendation.
8. Explains why.

The recommendation includes:

- Recommended card
- Expected rewards
- Supporting calculations
- Relevant reward rules
- Source citations
- Confidence score

---

# High-Level AI Workflow

```
User Query
      │
      ▼
Intent Detection
      │
      ▼
Load User Context
      │
      ▼
Retrieve Latest Knowledge
      │
      ▼
Apply Rule Engine
      │
      ▼
Graph Optimization
      │
      ▼
AI Planning
      │
      ▼
Generate Recommendation
      │
      ▼
Evidence + Explanation
      │
      ▼
User
```

---

# Product Workflow

```
User
   │
   ▼
Portfolio
   │
   ▼
Recommendation Request
   │
   ▼
Knowledge Retrieval
   │
   ▼
Rule Evaluation
   │
   ▼
Graph Search
   │
   ▼
Agent Reasoning
   │
   ▼
Recommendation
   │
   ▼
Explanation
```

---

# Why This Architecture?

The product intentionally separates deterministic logic from AI reasoning.

| Component | Responsibility |
|------------|----------------|
| Rule Engine | Exact calculations |
| Graph Engine | Transfer optimization |
| Hybrid Retrieval | Latest knowledge |
| Multi-Agent System | Planning and reasoning |
| Memory | Personalization |
| LLM | Natural language interaction |

Each component has a clearly defined responsibility, making the system easier to scale, evaluate, and maintain.

---

# Example Recommendation

**User Goal**

Book a five-night stay in Singapore.

**Recommendation**

- Transfer HDFC Reward Points to Marriott Bonvoy.
- Delay the transfer until the upcoming bonus promotion.
- Use Axis Atlas for remaining travel bookings to unlock the annual milestone.
- Purchase hotel vouchers through SmartBuy before reaching the monthly reward cap.

**Supporting Evidence**

- Current transfer ratio
- Marriott redemption estimate
- SmartBuy reward cap
- Remaining milestone spend
- Official documentation links
- Confidence score

---

# What Makes RewardsPilotOS Different?

RewardsPilotOS is not:

- A rewards calculator
- A card comparison website
- A loyalty tracker
- A travel booking platform

RewardsPilotOS is an AI decision engine that combines retrieval, structured rules, graph optimization, and personalized reasoning to recommend the next best action for every stage of a user's rewards journey.

Every recommendation answers a single question:

> **"Given my portfolio, goals, and the latest reward ecosystem, what should I do next?"**

---

# 10. Core Product Capabilities

## Objective

Define the core capabilities of RewardsPilotOS. These capabilities represent the primary value delivered to users and form the foundation for product requirements, system architecture, and AI workflows.

---

# Product Capability Map

RewardsPilotOS consists of eight primary capabilities.

```
                      RewardsPilotOS
                             │
    ┌────────────────────────┼────────────────────────┐
    │                        │                        │
Portfolio              Spend Optimization      Benefits Intelligence
Management
    │                        │                        │
    ├────────────────────────┼────────────────────────┤
    │                        │                        │
Transfer              Redemption            Knowledge Intelligence
Optimization          Intelligence
    │                        │                        │
    ├────────────────────────┼────────────────────────┤
    │                        │
AI Decision Engine      Notifications & Monitoring
```

---

# Capability 1: Portfolio Management

## Purpose

Maintain a unified view of the user's rewards ecosystem.

---

## Inputs

- Credit cards owned
- Reward balances
- Airline memberships
- Hotel memberships
- Spending preferences
- Travel goals
- Annual fee information

---

## Outputs

- Portfolio dashboard
- Reward balances
- Active benefits
- Milestone tracking
- Point expiry
- Personalized context for AI

---

## Example

Portfolio

- HDFC Infinia
- Axis Atlas
- Amex Platinum Travel

Reward balances

- HDFC Reward Points
- EDGE Miles
- Membership Rewards
- Marriott Bonvoy Points

---

# Capability 2: Spend Optimization

## Purpose

Recommend the optimal payment method for every purchase.

---

## Example Questions

- Which card should I use for groceries?
- Which card should I use for insurance?
- Which card should I use for a ₹1 lakh laptop?
- Should I purchase Amazon vouchers through SmartBuy first?

---

## Factors Considered

- Reward rate
- Accelerated rewards
- Merchant category
- SmartBuy eligibility
- Monthly reward caps
- Milestone progress
- Ongoing promotions

---

## Output

Recommended card with a detailed explanation.

---

# Capability 3: Benefits Intelligence

## Purpose

Ensure users maximize every benefit included with their cards.

---

## Examples

- Lounge visits remaining
- Complimentary hotel nights
- Dining offers
- Golf benefits
- Travel insurance
- Concierge services
- Milestone benefits

---

## Example Recommendation

"You have not used your quarterly lounge access."

---

# Capability 4: Transfer Optimization

## Purpose

Identify the highest-value transfer path across reward ecosystems.

---

## Supported Programs

### Airlines

- Air India Maharaja Club
- KrisFlyer
- British Airways Executive Club
- Flying Blue
- Qatar Privilege Club

### Hotels

- Marriott Bonvoy
- Accor Live Limitless
- Hilton Honors
- IHG One Rewards

---

## Optimization Factors

- Transfer ratio
- Transfer bonus
- Historical redemption value
- User preferences
- Expiry
- Availability

---

# Capability 5: Redemption Intelligence

## Purpose

Recommend the best redemption strategy.

---

## Example

Instead of:

Redeem points for vouchers.

Recommend:

Transfer to Marriott Bonvoy and redeem for a five-night stay worth significantly higher value.

---

## Recommendation Includes

- Expected value
- Point requirement
- Opportunity cost
- Supporting calculations
- Confidence score

---

# Capability 6: Knowledge Intelligence

## Purpose

Maintain an always-updated knowledge base.

---

## Knowledge Sources

### Banks

- HDFC
- Axis
- Amex
- HSBC
- ICICI
- SBI

### Loyalty Programs

- Marriott
- Accor
- KrisFlyer
- Flying Blue
- Qatar Airways

### Community

- TechnoFino
- Reddit
- FlyerTalk

### Official Documentation

- Terms and conditions
- Benefit guides
- Reward catalogs

---

## Responsibilities

- Crawl
- Parse
- Chunk
- Embed
- Version
- Detect changes

---

# Capability 7: AI Decision Engine

## Purpose

Convert user intent into personalized recommendations.

---

## Example Questions

- Which card should I use?
- Should I transfer points now?
- Is this annual fee worth paying?
- Am I wasting rewards?
- Which hotel should I book?

---

## AI Responsibilities

- Intent understanding
- Planning
- Knowledge retrieval
- Rule reasoning
- Graph optimization
- Recommendation generation
- Explanation generation

---

# Capability 8: Monitoring & Notifications

## Purpose

Proactively notify users when opportunities arise.

---

## Examples

- SmartBuy cap almost reached
- New transfer bonus
- Reward expiry
- Better redemption available
- Annual fee approaching
- New airline partner added
- Benefit unused
- Promotion ending soon

---

# Capability Relationships

```
Portfolio
      │
      ▼
Knowledge Retrieval
      │
      ▼
Rule Engine
      │
      ▼
Graph Optimization
      │
      ▼
AI Planning
      │
      ▼
Recommendation
      │
      ▼
Notification
```

---

# Product Design Principles

Every capability should satisfy the following principles.

## Explainable

Every recommendation includes supporting evidence.

---

## Personalized

Every recommendation uses user-specific context.

---

## Fresh

Knowledge reflects the latest available reward rules.

---

## Deterministic Where Possible

Rule-based calculations should never rely on LLM reasoning.

---

## AI Where Valuable

Use AI only for planning, personalization, summarization, and explanation.

---

# Summary

These capabilities define the functional scope of RewardsPilotOS and establish the foundation for the Product Requirements Document, system architecture, and AI implementation.

Each capability maps directly to one or more backend services, AI agents, APIs, and evaluation metrics described in later sections of this specification.

---

# 11. Feature Prioritization

## Objective

Prioritize product capabilities for the MVP based on customer value, engineering complexity, AI impact, and implementation feasibility.

The objective is to deliver the smallest product that demonstrates meaningful user value while showcasing modern AI system design.

---

# Prioritization Framework

Two prioritization frameworks are used:

- MoSCoW Prioritization
- RICE Scoring

MoSCoW determines release priority.

RICE helps compare competing features objectively.

---

# MoSCoW Prioritization

## Must Have

These features are essential for the MVP.

### User Management

- User profile
- Owned cards
- Reward balances (manual entry)
- Travel preferences
- Spending preferences

---

### Portfolio Dashboard

- Card overview
- Reward balances
- Loyalty programs
- Active benefits

---

### Spend Optimization

- Best card recommendation
- Reward calculation
- Category optimization
- Merchant optimization
- SmartBuy optimization
- Monthly reward cap tracking

---

### Knowledge Platform

- Reward program knowledge base
- Bank documentation
- Transfer partners
- Benefit guides
- Promotion tracking

---

### AI Decision Engine

- Natural language queries
- Personalized recommendations
- Explainable reasoning
- Supporting citations

---

### Transfer Optimization

- Airline transfer partners
- Hotel transfer partners
- Graph-based path optimization

---

### Rule Engine

- Reward calculations
- Transfer ratios
- Milestone tracking
- Eligibility rules
- Reward caps

---

## Should Have

These features significantly improve the experience but are not required for the MVP.

- Point expiry tracking
- Benefit utilization tracking
- Promotion alerts
- Recommendation history
- Recommendation explanations with visual breakdowns
- Personalized dashboard

---

## Could Have

These features are planned after the MVP.

- Statement parsing
- OCR
- Email parsing
- Lounge visit tracking
- Annual fee recommendations
- Spending forecasts
- Milestone predictions
- Budget planning
- Mobile application

---

## Won't Have (MVP)

The following capabilities are intentionally excluded.

- Automatic bank integrations
- Direct reward balance synchronization
- Credit card applications
- Travel booking
- Financial planning
- Investment recommendations
- Automated transactions
- Reward transfers
- Flight bookings

---

# RICE Prioritization

| Feature | Reach | Impact | Confidence | Effort | Priority |
|----------|------:|-------:|-----------:|-------:|----------|
| Spend Optimization | High | High | High | Medium | Very High |
| Portfolio Dashboard | High | High | High | Low | Very High |
| AI Decision Engine | High | High | Medium | High | Very High |
| Knowledge Platform | High | High | Medium | High | Very High |
| Rule Engine | High | High | High | Medium | Very High |
| Transfer Optimization | Medium | High | Medium | Medium | High |
| Point Expiry | Medium | Medium | High | Low | Medium |
| Notifications | Medium | Medium | Medium | Medium | Medium |
| Statement Parsing | Low | High | Low | Very High | Low |
| OCR | Low | Medium | Medium | High | Low |
| Auto Sync | Medium | High | Low | Very High | Low |

---

# MVP Definition

The MVP should answer one question exceptionally well.

> **"Given my cards, spending goals, reward balances, and the latest reward rules, what should I do next?"**

Everything included in the MVP directly contributes to answering this question.

---

# MVP User Journey

A user should be able to:

1. Create a profile.
2. Add owned credit cards.
3. Enter reward balances.
4. Ask a question in natural language.
5. Receive a personalized recommendation.
6. View supporting calculations.
7. View cited reward rules.
8. Understand why the recommendation was generated.

---

# Why Certain Features Were Deferred

## Automatic Bank Integration

Reason

Requires secure authentication, API availability, and significant engineering effort.

Manual input is sufficient to validate product-market fit.

---

## Statement Parsing

Reason

Useful for reducing friction but does not improve recommendation quality.

---

## OCR

Reason

Improves onboarding but is not essential for the recommendation engine.

---

## Travel Booking

Reason

RewardsPilotOS focuses on decision support rather than transaction execution.

---

## Mobile Application

Reason

A responsive web application is sufficient for validating the MVP.

---

# Engineering Priorities

The implementation order should maximize learning while minimizing engineering risk.

## Phase 1

Foundation

- Authentication
- Database
- Portfolio management

---

## Phase 2

Knowledge Platform

- Crawlers
- RAG pipeline
- Rule engine

---

## Phase 3

Decision Intelligence

- Graph optimization
- AI agents
- Recommendation engine

---

## Phase 4

Product Experience

- Dashboard
- Chat interface
- Recommendation history

---

## Phase 5

Evaluation

- AI evaluation
- Retrieval evaluation
- Product metrics
- Performance testing

---

# Success Criteria

The MVP is successful if it can consistently generate personalized, explainable, and evidence-backed recommendations that save users time while increasing the value they derive from their rewards portfolio.

---

# 12. Product Requirements Document (PRD)

### Document Information

| Field | Value |
|-------|-------|
| Product | RewardsPilotOS |
| Version | 1.0 |
| Status | Draft |
| Author | Tanisha Garg |
| Product Category | AI-powered Credit Card Rewards Decision Engine |

---

## 1. Overview

### Purpose

This Product Requirements Document (PRD) defines the functional and non-functional requirements for RewardsPilotOS. It serves as the primary implementation document for engineering, design, AI, and product teams.

The objective of RewardsPilotOS is to help users maximize the lifetime value of every credit card they own by providing personalized, explainable, and evidence-backed recommendations for spending, benefit utilization, point transfers, and reward redemptions.

Rather than functioning as a reward calculator or loyalty tracker, RewardsPilotOS acts as an intelligent decision engine that combines deterministic rule evaluation with AI reasoning.

---

## 2. Problem Statement

Managing multiple premium credit cards has become increasingly complex.

Users today must navigate:

- Multiple reward currencies
- Dynamic earning structures
- Merchant-specific offers
- Monthly reward caps
- Milestone rewards
- Airline transfer partners
- Hotel transfer partners
- Promotional campaigns
- Benefit utilization rules

This information is fragmented across bank websites, loyalty programs, blogs, PDFs, and community forums.

As a result, users spend significant time researching before making decisions and still risk selecting suboptimal earning or redemption strategies.

Current solutions provide information.

RewardsPilotOS provides decisions.

---

## 3. Vision

Enable every credit card user to make the optimal rewards decision with minimal effort and complete confidence.

---

## 4. Product Goals

The MVP focuses on five primary goals.

### Goal 1

Help users choose the best card for every purchase.

---

### Goal 2

Help users maximize long-term reward earnings.

---

### Goal 3

Help users optimize airline and hotel transfers.

---

### Goal 4

Reduce the time spent researching rewards programs.

---

### Goal 5

Build trust through transparent and explainable AI recommendations.

---

## 5. Success Metrics

### Business Metrics

Although this is a portfolio project, the product should define measurable success metrics.

| Metric | Target |
|---------|--------|
| Recommendation Acceptance Rate | >70% |
| Weekly Active Users | Increasing trend |
| Average Session Duration | >5 minutes |
| Returning Users | >40% |
| Recommendation Satisfaction | >4.5/5 |

---

### Product Metrics

| Metric | Description |
|----------|-------------|
| Recommendation Generated | Number of successful recommendations |
| Recommendation Viewed | Recommendation opened by user |
| Recommendation Accepted | User follows recommendation |
| Recommendation Rejected | User explicitly ignores recommendation |
| Recommendation Saved | User bookmarks recommendation |
| Recommendation Shared | User shares recommendation |

---

### AI Metrics

| Metric | Target |
|----------|---------|
| Retrieval Precision | >90% |
| Citation Coverage | 100% |
| Hallucination Rate | <2% |
| Rule Accuracy | 100% |
| Graph Search Accuracy | 100% |
| Recommendation Confidence | Reported for every response |

---

## 6. User Stories

### Epic 1 — Portfolio Management

#### Story 1

**As a** premium credit card user,

**I want** to add all my cards,

**so that** RewardsPilotOS understands my complete portfolio.

---

#### Story 2

**As a** user,

**I want** to update my reward balances,

**so that** recommendations are personalized.

---

### Epic 2 — Spend Optimization

#### Story 3

**As a** user,

**I want** to ask,

> Which card should I use for this purchase?

**so that** I maximize rewards.

---

#### Story 4

**As a** user,

**I want** to understand why a card is recommended,

**so that** I trust the recommendation.

---

### Epic 3 — Transfer Optimization

#### Story 5

**As a** traveler,

**I want** to compare multiple airline transfer partners,

**so that** I maximize redemption value.

---

#### Story 6

**As a** traveler,

**I want** to compare hotel transfer partners,

**so that** I obtain the highest value per point.

---

### Epic 4 — Benefit Utilization

#### Story 7

**As a** cardholder,

**I want** reminders for unused benefits,

**so that** I maximize the value of my annual fee.

---

### Epic 5 — AI Assistant

#### Story 8

**As a** user,

**I want** to ask questions in natural language,

**so that** I don't need to learn reward rules manually.

---

## 7. Product Scope

### MVP

The MVP supports:

#### Issuers

- HDFC
- Axis
- American Express

---

#### Capabilities

- Portfolio management
- Spend optimization
- SmartBuy optimization
- Transfer optimization
- Hotel recommendations
- Airline recommendations
- AI assistant
- Explainable recommendations
- Manual reward balance management

---

### Out of Scope

The MVP intentionally excludes:

- Bank account integration
- Automatic reward synchronization
- Flight booking
- Hotel booking
- Reward transfers
- Financial planning
- Credit card applications
- Investment recommendations

These capabilities may be considered in future releases but are not required to validate the core product hypothesis.

---

## 8. Core Product Requirements

Every recommendation generated by RewardsPilotOS must satisfy the following requirements.

#### Accurate

Recommendations must correctly apply all relevant reward rules.

---

#### Personalized

Recommendations must consider the user's portfolio, preferences, balances, and goals.

---

#### Explainable

Every recommendation must include:

- Reasoning
- Supporting calculations
- Source citations
- Confidence score
- Last verified timestamp

---

#### Fresh

Recommendations should use the latest available reward rules and program information.

---

#### Deterministic Where Possible

Business rules such as reward calculations, transfer ratios, milestone tracking, and eligibility checks must be handled by deterministic services rather than the LLM.

---

#### Human Controlled

RewardsPilotOS recommends actions.

Users remain responsible for all financial decisions and transactions.

---

## 9. Assumptions

The MVP assumes:

- Users are willing to manually enter reward balances.
- Official documentation is available for supported issuers.
- Reward rules can be represented using structured business logic.
- Users value explainability over full automation.
- Publicly available information is sufficient to generate meaningful recommendations.

---

## 10. Risks

| Risk | Mitigation |
|------|------------|
| Reward rules change frequently | Freshness-aware knowledge pipeline |
| Hallucinated AI responses | Hybrid Retrieval + Rule Engine |
| Incorrect recommendations | Deterministic business rules |
| User trust | Transparent explanations and citations |
| Manual data entry | Simple onboarding with future automation roadmap |

---

## 11. Functional Requirements

This section defines the functional behavior of every major capability in RewardsPilotOS.

Each requirement includes:

- Objective
- Business Value
- User Stories
- Functional Behavior
- Inputs
- Outputs
- Business Rules
- Acceptance Criteria
- Edge Cases
- API Implications
- AI Dependencies
- Failure Modes
- Future Enhancements

---

## FR-001 Portfolio Management

### Objective

Provide a centralized representation of the user's rewards ecosystem that serves as the foundation for all personalized recommendations.

Every recommendation generated by RewardsPilotOS depends on an accurate understanding of the user's portfolio.

---

### Business Value

Without portfolio context, recommendations become generic.

Portfolio Management enables:

- Personalized recommendations
- Cross-card optimization
- Reward balance tracking
- Benefit utilization
- Milestone tracking
- Long-term planning

This is the foundation of the recommendation engine.

---

### User Stories

#### Story 1

As a user,

I want to add all my credit cards,

so that RewardsPilotOS understands my portfolio.

---

#### Story 2

As a user,

I want to edit my reward balances,

so that recommendations remain accurate.

---

#### Story 3

As a user,

I want to define my travel preferences,

so that recommendations match my goals.

---

### Functional Requirements

The system shall allow users to:

- Add one or more credit cards.
- Edit card information.
- Remove cards.
- Enable or disable cards.
- Store annual fee information.
- Store reward balances.
- Store loyalty memberships.
- Store travel preferences.
- Store preferred airlines.
- Store preferred hotel chains.
- Store spending preferences.

---

The system shall maintain:

- Total portfolio value
- Total reward balances
- Active cards
- Annual fee summary
- Benefit utilization
- Milestone progress

---

### Inputs

User profile

Owned cards

Reward balances

Loyalty memberships

Travel goals

Preferences

---

### Outputs

Portfolio Summary

Card Summary

Reward Dashboard

Context supplied to AI agents

Context supplied to Rule Engine

Context supplied to Graph Engine

---

### Business Rules

A portfolio may contain multiple cards.

A reward currency belongs to one issuer.

Users may own multiple loyalty memberships.

Balances must never become negative.

Inactive cards should be excluded from recommendations unless explicitly requested.

---

### Acceptance Criteria

✓ Multiple cards supported

✓ Reward balances persist

✓ Portfolio loads within two seconds

✓ Portfolio updates immediately after edits

✓ AI receives latest portfolio context

---

### Edge Cases

Duplicate cards

Zero balances

Expired cards

Closed accounts

Unknown reward balance

Missing travel preferences

---

### API Endpoints

POST /portfolio/cards

GET /portfolio

PATCH /portfolio/cards/{id}

DELETE /portfolio/cards/{id}

---

### Database Tables

users

cards

user_cards

reward_balances

travel_preferences

hotel_preferences

airline_preferences

---

### AI Dependencies

Memory Service

Recommendation Agent

Planner Agent

Graph Engine

Rule Engine

---

### Failure Modes

Invalid reward balance

Duplicate card

Unknown issuer

Corrupted profile

Missing preferences

---

### Future Enhancements

Automatic statement parsing

Bank integrations

Balance synchronization

OCR onboarding

---

## FR-002 Spend Optimization Engine

### Objective

Recommend the optimal payment strategy for every purchase while maximizing the user's long-term rewards.

Unlike traditional reward calculators, the objective is not to maximize immediate points earned.

The objective is to maximize the lifetime value of the user's entire rewards portfolio.

---

### Business Value

Spend optimization is expected to become the most frequently used capability within RewardsPilotOS.

Users make spending decisions every day.

Helping users choose the right card consistently creates recurring engagement.

---

### User Stories

As a user,

I want to know which card I should use before making a purchase.

---

As a user,

I want the recommendation to explain why one card is better than another.

---

As a user,

I want the recommendation to account for milestone rewards instead of only immediate earnings.

---

### Supported Purchase Types

Online Shopping

Offline Shopping

Travel

Hotels

Flights

Dining

Fuel

Utilities

Insurance

Education

Rent

Gift Cards

Government Payments

Electronics

Luxury Purchases

Subscriptions

---

### Inputs

Purchase Amount

Merchant

Merchant Category

Purchase Date

Payment Channel

Current Promotions

Portfolio

Reward Balances

Milestone Progress

Monthly Spend

---

### Decision Factors

Base Reward Rate

Accelerated Reward Rate

Merchant Offers

SmartBuy Multipliers

Voucher Multipliers

Reward Caps

Remaining Monthly Limits

Annual Milestones

Transfer Potential

Benefit Utilization

Current Promotions

Travel Goals

Historical User Preferences

---

### Recommendation Logic

The recommendation engine should evaluate every eligible card.

For every candidate card it should calculate:

Immediate rewards

Future milestone value

Remaining milestone spend

Monthly cap utilization

Reward currency value

Transfer flexibility

Expected redemption value

Long-term portfolio impact

The highest scoring option becomes the recommended strategy.

---

### Example Recommendation

User

Owns:

HDFC Infinia

Axis Atlas

Amex Platinum Travel

Purchase

₹82,000 laptop

Recommendation

Purchase Amazon Shopping Voucher through SmartBuy using HDFC Infinia.

Expected Reward Points

XXXXX

Monthly Cap Remaining

XXXXX

Milestone Progress

XXXXX

Alternative Recommendation

Use Axis Atlas if preserving HDFC monthly SmartBuy capacity for future travel bookings.

---

### Outputs

Recommended Card

Expected Reward Points

Expected Value

Reasoning

Supporting Calculations

Reward Rules Used

Sources

Confidence Score

---

### Acceptance Criteria

Recommendations generated within five seconds.

Correct reward calculations.

Monthly reward caps respected.

Milestone calculations correct.

Supporting citations included.

Confidence score displayed.

---

### Edge Cases

Merchant unknown

Promotion expired

Reward cap reached

Multiple cards produce identical value

Insufficient information

Conflicting reward rules

---

### API

POST /recommend/spend

GET /recommend/history

---

### Dependencies

Planner Agent

Tool Registry

Knowledge Platform

Rule Engine

Graph Engine

Memory Service

LLM

---

### Failure Modes

Missing reward rules

Stale promotion

Knowledge conflict

Graph unavailable

Rule engine failure

LLM timeout

---

### Future Enhancements

Real-time offer detection

UPI optimization

Wallet optimization

Corporate card support

Family portfolio optimization

---

## FR-003 Transfer Optimization Engine

### Objective

Identify the optimal path for transferring reward points from issuer reward currencies to airline and hotel loyalty programs while maximizing expected redemption value.

The engine should evaluate all valid transfer paths and recommend the one that best aligns with the user's goals.

---

### Business Value

Transfer decisions are among the highest-value and least reversible actions users make.

A poor transfer can permanently reduce the value of accumulated rewards.

RewardsPilotOS should help users make transfer decisions confidently by combining deterministic calculations, graph optimization, and AI reasoning.

---

### User Stories

#### Story 1

As a traveler,

I want to know whether I should transfer my points today,

so that I avoid making irreversible mistakes.

---

#### Story 2

As a user,

I want to compare multiple airline and hotel partners,

so that I maximize redemption value.

---

#### Story 3

As a user,

I want transfer recommendations to consider my future travel goals,

so that I don't optimize only for today's booking.

---

### Inputs

Portfolio

Reward Balances

Transfer Ratios

Transfer Bonuses

Airline Programs

Hotel Programs

Travel Goals

Preferred Airlines

Preferred Hotels

Destination

Travel Dates

Current Promotions

---

### Functional Requirements

The system shall:

- Identify all valid transfer partners.
- Calculate transferable balances.
- Apply current transfer ratios.
- Apply active transfer bonuses.
- Estimate expected redemption value.
- Compare airline and hotel options.
- Rank transfer paths.
- Explain why a path is recommended.

---

### Optimization Factors

Transfer Ratio

Transfer Bonus

Historical Redemption Value

Award Availability (future)

Program Flexibility

Point Expiry

User Preferences

Travel Goals

Expected CPP (Cents Per Point)

Opportunity Cost

---

### Outputs

Recommended Transfer Path

Alternative Paths

Estimated Value

Expected Redemption Value

Supporting Calculations

Confidence Score

Sources

---

### Example

User owns:

- HDFC Reward Points
- Axis EDGE Miles

Goal:

Five nights in Singapore.

Recommendation:

Transfer HDFC Reward Points to Marriott Bonvoy.

Reason:

- Highest expected redemption value.
- Better flexibility than airline transfer.
- Active transfer bonus.
- Matches user's preferred hotel chain.

Alternative:

Transfer Axis EDGE Miles to KrisFlyer for business-class flights.

---

### Acceptance Criteria

- All supported transfer partners evaluated.
- Transfer ratios correctly applied.
- Promotions considered.
- Recommendation includes explanation.
- Graph search completes within acceptable latency.

---

### Edge Cases

Transfer partner temporarily unavailable.

Transfer bonus expires today.

Insufficient point balance.

Multiple equivalent paths.

Conflicting reward rules.

---

### API

POST /recommend/transfer

GET /transfer/options

GET /transfer/history

---

### Dependencies

Knowledge Platform

Rule Engine

Graph Engine

Recommendation Agent

Portfolio Service

---

### Future Enhancements

Award availability integration.

Predictive transfer timing.

Historical redemption analytics.

Transfer simulation.

---

## FR-004 Redemption Intelligence

### Objective

Recommend the highest-value redemption strategy based on the user's portfolio, goals, and the latest reward ecosystem.

Redemption recommendations should optimize realized value rather than simply minimizing point usage.

---

### Business Value

Many users earn points effectively but redeem them inefficiently.

RewardsPilotOS should bridge this gap by identifying high-value redemption opportunities.

---

### User Stories

#### Story 1

As a user,

I want to know the best way to redeem my points,

so that I maximize value.

---

#### Story 2

As a traveler,

I want multiple redemption options,

so that I can choose based on flexibility.

---

#### Story 3

As a beginner,

I want the recommendation explained,

so that I learn how reward ecosystems work.

---

### Inputs

Reward Balances

Transfer Options

Destination

Travel Dates

Hotel Preferences

Airline Preferences

Current Promotions

Portfolio Context

---

### Functional Requirements

The system shall:

- Compare all supported redemption options.
- Estimate redemption value.
- Estimate value per point.
- Compare cash vs points.
- Explain tradeoffs.
- Recommend the optimal strategy.

---

### Recommendation Should Include

Recommended Redemption

Alternative Redemptions

Estimated Savings

Value Per Point

Opportunity Cost

Supporting Evidence

Confidence Score

---

### Example

Goal:

Weekend trip to Dubai.

Recommendation:

Transfer points to Marriott Bonvoy instead of redeeming for vouchers.

Reason:

Expected value is approximately 2.4× higher.

Alternative:

Transfer to Flying Blue if the user's priority is premium cabin travel.

---

### Acceptance Criteria

- Multiple redemption options evaluated.
- Recommendation is personalized.
- Sources cited.
- Calculations visible.
- Confidence reported.

---

### Edge Cases

Insufficient balance.

No suitable transfer partner.

Expired promotion.

Destination unsupported.

Incomplete user preferences.

---

### API

POST /recommend/redeem

GET /redeem/options

---

### Dependencies

Transfer Engine

Knowledge Platform

Rule Engine

Graph Engine

Planner Agent

Recommendation Agent

---

### Future Enhancements

Dynamic award pricing.

Live hotel inventory.

Flight award inventory.

Calendar-based redemption planning.

Cash vs points optimizer.

---

## FR-005 AI Recommendation Engine

### Objective

Generate personalized, explainable, and evidence-backed recommendations by combining user context, deterministic business rules, graph optimization, and LLM reasoning.

The Recommendation Engine acts as the orchestration layer between the user and the underlying intelligence components.

---

### Business Value

Users should never need to manually research multiple websites before making a rewards decision.

Instead, they ask a question in natural language and receive a personalized recommendation backed by calculations and official sources.

---

### User Stories

#### Story 1

As a user,

I want to ask questions naturally,

so that I don't need to understand complex rewards terminology.

---

#### Story 2

As a traveler,

I want recommendations tailored to my travel goals,

so that suggestions are relevant.

---

#### Story 3

As an experienced rewards user,

I want supporting evidence,

so that I trust the recommendation.

---

### Example Questions

Which card should I use for a ₹70,000 insurance payment?

Should I buy Amazon vouchers through SmartBuy?

Should I transfer my HDFC points now?

How should I book my Singapore trip?

Am I wasting any benefits?

Which card should I close?

Should I renew my annual fee?

---

### Functional Requirements

The Recommendation Engine shall:

- Understand user intent.
- Retrieve relevant knowledge.
- Load portfolio context.
- Apply deterministic business rules.
- Evaluate transfer paths.
- Generate recommendations.
- Explain reasoning.
- Provide citations.
- Report confidence.

---

### Recommendation Structure

Every recommendation must include:

#### Recommendation Summary

One concise recommendation.

---

#### Supporting Reasoning

Explain why the recommendation was selected.

---

#### Supporting Calculations

Display:

- Reward Points
- Expected Redemption Value
- Remaining Reward Caps
- Milestone Progress

---

#### Sources

List supporting documentation.

---

#### Confidence

High

Medium

Low

---

#### Assumptions

Clearly state assumptions made during reasoning.

---

### Recommendation Pipeline

User Query

↓

Intent Detection

↓

Portfolio Context

↓

Knowledge Retrieval

↓

Rule Evaluation

↓

Graph Optimization

↓

Planner Agent

↓

Recommendation Generation

↓

Explanation Generation

↓

Response

---

### Acceptance Criteria

Recommendations generated in under five seconds.

Recommendation includes explanation.

Recommendation includes citations.

Recommendation includes confidence score.

Business rules applied correctly.

---

### Edge Cases

Missing portfolio.

Missing reward balance.

Knowledge unavailable.

Conflicting rules.

Insufficient context.

Ambiguous query.

---

### APIs

POST /recommend

GET /recommend/history

GET /recommend/{id}

---

### Dependencies

Portfolio Service

Knowledge Platform

Graph Engine

Rule Engine

Planner Agent

Memory Service

LLM

---

### Failure Modes

LLM unavailable.

Knowledge retrieval failure.

Rule conflict.

Timeout.

Missing user context.

---

### Future Enhancements

Recommendation feedback loop.

A/B testing.

Continuous learning.

Personalized recommendation ranking.

Recommendation comparison mode.

---

## FR-006 Knowledge Platform

### Objective

Maintain a continuously updated knowledge base containing reward rules, transfer partners, promotions, benefit guides, and issuer documentation.

This platform serves as the source of truth for RewardsPilotOS.

---

### Business Value

The quality of recommendations depends directly on the freshness and completeness of the knowledge base.

Without a reliable knowledge platform, recommendations quickly become outdated.

---

### Supported Knowledge Sources

#### Banks

HDFC

Axis

American Express

HSBC

ICICI

SBI

---

#### Loyalty Programs

Marriott Bonvoy

Accor Live Limitless

Hilton Honors

IHG One Rewards

Air India Maharaja Club

Singapore Airlines KrisFlyer

Flying Blue

British Airways Executive Club

Qatar Privilege Club

---

#### Official Sources

Terms & Conditions

Reward Catalogs

Benefit Guides

Transfer Partner Documentation

Promotion Pages

FAQs

---

#### Community Sources

TechnoFino

FlyerTalk

Reddit

Official Blogs

Community knowledge is supplementary and should never override official documentation.

---

### Functional Requirements

The platform shall:

- Crawl supported sources.
- Parse structured information.
- Detect changes.
- Version documents.
- Generate embeddings.
- Maintain metadata.
- Track freshness.
- Support semantic search.

---

### Metadata

Every knowledge chunk should include:

Source

Issuer

Document Type

Category

Effective Date

Last Verified

Version

Confidence

URL

---

### Freshness Policy

Critical rules

Refresh daily.

Promotions

Refresh every six hours.

Transfer ratios

Refresh daily.

Benefit guides

Refresh weekly.

Static documentation

Refresh monthly.

---

### Acceptance Criteria

Knowledge indexed successfully.

Metadata stored.

Embeddings generated.

Freshness timestamp recorded.

Version history maintained.

---

### APIs

POST /crawl

POST /ingest

GET /knowledge/search

GET /knowledge/document/{id}

---

### Dependencies

Crawler

Parser

Embedding Service

Vector Database

Knowledge Database

---

### Failure Modes

Source unavailable.

Parser failure.

Duplicate documents.

Stale information.

Embedding generation failure.

---

### Future Enhancements

Automatic document classification.

Promotion extraction.

Change summarization.

Knowledge quality scoring.

Knowledge approval workflow.

Crawler
      │
      ▼
Parser
      │
      ▼
Knowledge Service
      │
 ┌────┴─────────────┐
 │                  │
Structured DB    Vector DB
 │                  │
 └──────┬───────────┘
        ▼
Recommendation Engine

---

## FR-007 Rule Engine

### Objective

Provide deterministic evaluation of all business rules, ensuring recommendations are mathematically correct, reproducible, and independent of LLM reasoning.

The Rule Engine is the authoritative source for calculations involving rewards, eligibility, caps, milestones, transfer ratios, and benefit logic.

---

### Business Value

Credit card rewards are governed by explicit rules.

These calculations should never depend on probabilistic AI reasoning.

The Rule Engine guarantees correctness while allowing AI agents to focus on planning and personalization.

---

### User Stories

#### Story 1

As a user,

I want reward calculations to be accurate,

so that I can trust every recommendation.

---

#### Story 2

As a user,

I want recommendations to respect issuer restrictions,

so that I do not exceed earning caps or violate program rules.

---

### Responsibilities

The Rule Engine shall:

- Calculate reward points.
- Apply category multipliers.
- Apply SmartBuy multipliers.
- Apply voucher-specific earning rules.
- Track monthly earning caps.
- Track annual milestones.
- Evaluate transfer ratios.
- Validate transfer eligibility.
- Calculate expected redemption value.
- Apply issuer-specific exclusions.
- Apply promotional rules.

---

### Rule Categories

#### Reward Rules

- Base earning rate
- Accelerated earning rate
- Merchant-specific rewards
- Category-specific rewards

---

#### SmartBuy Rules

- Voucher multipliers
- Travel booking multipliers
- Monthly caps
- Merchant eligibility

---

#### Milestone Rules

- Annual spend targets
- Welcome bonuses
- Milestone rewards
- Renewal benefits

---

#### Transfer Rules

- Supported partners
- Transfer ratios
- Minimum transfer amount
- Maximum transfer amount
- Bonus promotions

---

#### Benefit Rules

- Lounge access
- Dining offers
- Golf benefits
- Insurance eligibility
- Hotel privileges

---

### Inputs

Portfolio

Purchase

Knowledge Platform

Current Promotions

Reward Balances

Travel Goals

---

### Outputs

Reward Calculations

Eligible Cards

Transfer Values

Benefit Eligibility

Milestone Progress

Rule Explanation

---

### Acceptance Criteria

✓ All calculations deterministic.

✓ Results reproducible.

✓ Rules versioned.

✓ Historical calculations reproducible using previous rule versions.

---

### Edge Cases

Promotion expires during calculation.

Multiple overlapping promotions.

Issuer changes reward policy.

Conflicting reward rules.

Unknown merchant category.

---

### APIs

POST /rules/evaluate

POST /rules/calculate

GET /rules/version

---

### Dependencies

Knowledge Platform

Portfolio Service

Graph Engine

---

### Future Enhancements

Rule simulator.

Historical rule playback.

Visual rule editor.

Administrative rule management.

---

## FR-008 Notification & Opportunity Engine

### Objective

Continuously monitor the user's portfolio and the external rewards ecosystem to proactively identify opportunities that increase long-term portfolio value.

Unlike traditional notification systems, RewardsPilotOS should notify users only when a recommendation creates meaningful value.

---

### Business Value

Many high-value opportunities are time-sensitive.

Users often miss:

- Limited-time transfer bonuses.
- Expiring reward points.
- Unused premium benefits.
- Annual milestones.
- SmartBuy cap utilization.
- Seasonal promotions.

The Opportunity Engine transforms RewardsPilotOS from a reactive assistant into a proactive decision engine.

---

### User Stories

#### Story 1

As a user,

I want to know when a better redemption opportunity becomes available,

so that I maximize value.

---

#### Story 2

As a user,

I want reminders before my points expire,

so that I never lose rewards.

---

#### Story 3

As a traveler,

I want alerts about transfer bonuses,

so that I transfer points at the optimal time.

---

### Notification Categories

#### Portfolio

- Point expiry
- Annual fee renewal
- Milestone progress
- Benefit utilization

---

#### Knowledge Updates

- New transfer partner
- Reward rule changes
- Promotion launched
- Promotion ending

---

#### Spending Opportunities

- SmartBuy recommendation
- Merchant promotion
- Category bonus

---

#### Travel Opportunities

- Hotel transfer bonus
- Airline transfer bonus
- Seasonal redemption opportunity

---

### Trigger Sources

Portfolio Changes

Knowledge Updates

Scheduled Jobs

User Activity

Promotion Detection

Rule Changes

---

### Functional Requirements

The engine shall:

- Monitor portfolio events.
- Monitor reward rule updates.
- Detect meaningful opportunities.
- Prioritize notifications.
- Suppress duplicate alerts.
- Explain why a notification was generated.

---

### Notification Structure

Title

Summary

Recommendation

Expected Benefit

Supporting Evidence

Source

Timestamp

Priority

---

### Priority Levels

Critical

High

Medium

Low

---

### Acceptance Criteria

Duplicate notifications suppressed.

Every notification includes supporting evidence.

Notifications generated only for actionable events.

Priority assigned correctly.

---

### APIs

GET /notifications

POST /notifications/read

POST /notifications/preferences

---

### Dependencies

Knowledge Platform

Portfolio Service

Recommendation Engine

Rule Engine

Memory Service

Scheduler

---

### Failure Modes

Duplicate alerts.

Stale promotion.

Missed opportunity.

Notification fatigue.

Conflicting recommendations.

---

### Future Enhancements

Personalized notification frequency.

Cross-device synchronization.

Email digests.

Weekly opportunity summaries.

Push notifications.

Calendar integration.

---

Knowledge Update
        │
        ▼
Portfolio Impact Analysis
        │
        ▼
Opportunity Detection
        │
        ▼
Rule Evaluation
        │
        ▼
Recommendation Generation
        │
        ▼
Notification

---

## 12. Non-Functional Requirements

This section defines the quality attributes of RewardsPilotOS.

Unlike functional requirements, these requirements specify how the system should behave rather than what features it provides.

---

## NFR-001 Performance

### Objective

Recommendations should be generated quickly enough to support interactive conversations.

---

### Requirements

Portfolio loading time

Target

< 2 seconds

---

Recommendation generation

Target

< 5 seconds

---

Knowledge retrieval

Target

< 500 ms

---

Rule Engine execution

Target

< 200 ms

---

Graph optimization

Target

< 500 ms

---

Dashboard rendering

Target

< 2 seconds

---

Search response

Target

< 1 second

---

## NFR-002 Reliability

The platform should provide consistent recommendations even during partial system failures.

---

### Requirements

Gracefully degrade if:

- LLM unavailable
- Vector database unavailable
- Graph Engine unavailable
- External knowledge source unavailable

---

Example

If the Knowledge Platform is temporarily unavailable,

the system should:

- use the latest verified knowledge snapshot
- warn the user that fresh verification could not be completed
- continue generating recommendations if confidence remains acceptable

---

## NFR-003 Explainability

Every recommendation must be explainable.

Users should understand:

- Why this recommendation was generated.
- Which rules were applied.
- Which assumptions were made.
- Which sources were consulted.
- Which alternatives were considered.

---

Every recommendation should contain:

Recommendation

↓

Reasoning

↓

Calculations

↓

Supporting Sources

↓

Confidence

---

## NFR-004 Freshness

Recommendations should reflect the latest available reward rules.

---

Knowledge freshness targets

| Data | Refresh Frequency |
|---------|----------------|
| Promotions | Every 6 hours |
| Transfer bonuses | Daily |
| Reward rules | Daily |
| Benefit guides | Weekly |
| Static documentation | Monthly |

---

Every retrieved document should expose:

Last verified

Knowledge version

Document source

Effective date

---

## NFR-005 Security

RewardsPilotOS should follow the principle of minimum required data.

---

The MVP should NOT store:

- Card numbers
- CVV
- OTP
- Internet banking credentials
- UPI PIN
- Transaction passwords

---

Instead, it stores:

- Card name
- Reward balances
- User preferences
- Loyalty memberships
- Portfolio metadata

---

Sensitive information should be encrypted at rest.

All communication should use HTTPS.

---

## NFR-006 Privacy

Users own their portfolio data.

The platform should:

- Allow data export.
- Allow permanent deletion.
- Explain stored information.
- Allow users to disable memory.

The AI should never use one user's portfolio to generate recommendations for another user.

---

## NFR-007 Scalability

The architecture should support adding new issuers without major system redesign.

Example

Adding HSBC should require:

- New crawler
- New reward rules
- New transfer graph nodes

No Recommendation Engine changes should be required.

---

Similarly,

adding Marriott promotions should not require backend code changes.

Only the Knowledge Platform should update.

---

## NFR-008 Maintainability

Business logic should remain independent of LLM prompts.

Rule changes should be implemented by updating:

Rule definitions

Knowledge documents

Configuration

NOT application code.

---

## NFR-009 Observability

Every recommendation should be traceable.

Log:

Recommendation ID

Timestamp

Knowledge Version

Rule Version

Retrieved Documents

Agent Trace

LLM Model

Latency

Confidence

---

Example

Recommendation #8932

↓

Knowledge Version 2026-08-12

↓

Rule Version 18

↓

Retrieved 6 Documents

↓

Planner Agent

↓

Transfer Agent

↓

Final Recommendation

---

## NFR-010 Availability

Target uptime

99%

The platform should remain usable even if:

Knowledge crawling fails.

Promotion crawling fails.

Community sources become unavailable.

---

## NFR-011 Accessibility

The application should support:

Keyboard navigation

Screen readers

Responsive layouts

Mobile browsers

High contrast mode

---

## NFR-012 Extensibility

The architecture should support future capabilities including:

Automatic statement parsing

Email parsing

OCR onboarding

Bank APIs

Mobile applications

International issuers

Additional loyalty programs

without redesigning the recommendation engine.

---

## 13. Security & Privacy

### Security Principles

RewardsPilotOS is a recommendation platform.

It is NOT a payment platform.

The system never executes financial transactions.

---

### Authentication

Users authenticate using:

Email

Google OAuth

Future

Apple Sign In

GitHub

---

### Authorization

Users may only access:

Their own portfolio

Their own recommendations

Their own balances

Their own history

---

### Data Encryption

Encrypt:

User preferences

Reward balances

Travel goals

Recommendation history

---

Never log:

Authentication tokens

Passwords

Sensitive credentials

---

### Data Retention

Recommendation history

12 months

Portfolio

Until user deletion

Knowledge

Versioned permanently

Logs

90 days

---

## 14. Analytics & Instrumentation

The system should measure product adoption and recommendation quality.

---

### Product Events

User Registered

Portfolio Created

Card Added

Recommendation Requested

Recommendation Viewed

Recommendation Accepted

Recommendation Dismissed

Notification Opened

Transfer Planned

---

### AI Events

Knowledge Retrieved

Rule Executed

Graph Search Completed

LLM Called

Recommendation Generated

Confidence Assigned

Citation Added

---

### System Metrics

Recommendation Latency

Retriever Latency

Graph Search Time

Rule Engine Time

LLM Response Time

Memory Retrieval Time

---

### Dashboard Metrics

Daily Active Users

Weekly Active Users

Most Asked Questions

Top Recommended Cards

Most Used Transfer Partner

Average Confidence

Recommendation Acceptance Rate

Average Session Duration

---

For every recommendation, automatically persist:
User Query

↓

Retrieved Documents

↓

Rule Outputs

↓

Graph Output

↓

Agent Trace

↓

Final Recommendation

↓

User Feedback

That single trace enables offline evaluation, regression testing, prompt comparisons, and future improvements. It also shows recruiters you're thinking beyond "it works" to "it can be measured and improved," which is a hallmark of production AI systems.

---

## 15. Error Handling & Failure Modes

### Objective

RewardsPilotOS should continue providing useful recommendations even when individual components fail. The system should gracefully degrade rather than returning generic errors.

---

## Error Handling Principles

The system should:

- Fail gracefully.
- Explain failures to users.
- Preserve user trust.
- Never fabricate information.
- Never hide uncertainty.

---

## Failure Categories

### Knowledge Failures

Examples

- Bank website unavailable
- Promotion page removed
- Parser failure
- Document ingestion failed

#### Expected Behavior

Use the most recently verified knowledge snapshot.

Display:

- Last verified timestamp
- Confidence reduction
- Explanation that fresh verification was unavailable

---

### Rule Engine Failures

Examples

- Reward rule missing
- Unknown merchant category
- Invalid reward configuration

#### Expected Behavior

Skip unsupported calculations.

Explain which calculation could not be completed.

Never estimate missing rule values using the LLM.

---

### Graph Engine Failures

Examples

- Transfer graph unavailable
- Invalid graph edge
- No transfer path exists

#### Expected Behavior

Inform the user that transfer optimization could not be completed.

Still provide rule-based recommendations if possible.

---

### LLM Failures

Examples

- Timeout
- Rate limit
- Model unavailable

#### Expected Behavior

Return deterministic recommendation without natural language explanation whenever possible.

---

### Memory Failures

Examples

- Missing preferences
- Corrupted profile
- Missing balances

#### Expected Behavior

Ask the user for the missing information instead of making assumptions.

---

## User Facing Errors

Error messages should be actionable.

Instead of

"Recommendation failed."

Display

"I couldn't verify the latest SmartBuy reward rules. The recommendation below is based on rules last verified 18 hours ago."

---

## 16. Release Plan

### Phase 1

Portfolio Foundation

Deliverables

- Authentication
- Portfolio
- Dashboard
- Reward balances

Success Criteria

User can create a complete portfolio.

---

### Phase 2

Knowledge Platform

Deliverables

- Crawlers
- Parser
- Knowledge Service
- Hybrid Retrieval

Success Criteria

Reward rules searchable with citations.

---

### Phase 3

Recommendation Engine

Deliverables

- Rule Engine
- Recommendation Engine
- Chat Interface

Success Criteria

Users receive explainable recommendations.

---

### Phase 4

Transfer Intelligence

Deliverables

- Graph Engine
- Transfer Planner
- Redemption Planner

Success Criteria

Users receive transfer recommendations.

---

### Phase 5

Opportunity Engine

Deliverables

- Rule Monitoring
- Promotion Detection
- Notifications

Success Criteria

Users receive proactive opportunities.

---

### Phase 6

Evaluation & Production Readiness

Deliverables

- AI evaluations
- Logging
- Dashboards
- Monitoring

Success Criteria

Recommendation quality is measurable and repeatable.

---

## 17. Definition of Done

A feature is considered complete only if all of the following conditions are satisfied.

### Product

- Requirements implemented.
- Acceptance criteria met.
- UX reviewed.

---

### Engineering

- Unit tests added.
- Integration tests passing.
- API documented.
- Performance targets achieved.

---

### AI

- Retrieval evaluated.
- Hallucination checks completed.
- Citations verified.
- Confidence scoring implemented.

---

### Data

- Knowledge indexed.
- Metadata validated.
- Freshness recorded.

---

### Observability

- Logs added.
- Metrics collected.
- Agent traces stored.

---

### Documentation

- README updated.
- API documented.
- Architecture updated.

---

## 18. Open Questions

The following questions remain intentionally open for future iterations.

### User Data

Should bank integrations be supported?

Current decision:

Manual portfolio management for MVP.

---

### Award Availability

Should live airline award inventory be integrated?

Deferred until post-MVP.

---

### Hotel Pricing

Should live hotel pricing be incorporated into redemption recommendations?

Future enhancement.

---

### Automatic Point Tracking

Should email parsing or statement parsing automatically update balances?

Deferred.

---

### Personalization

Should recommendations adapt based on historical user behavior?

Planned for future releases.

---

## 19. Future Roadmap

### Version 2

- HSBC support
- ICICI support
- SBI support
- Better dashboard
- Recommendation history

---

### Version 3

- OCR onboarding
- Email parsing
- Statement parsing
- Automatic balance updates
- Smart notification engine

---

### Version 4

- Family portfolios
- Shared rewards planning
- Business travelers
- Corporate cards

---

### Version 5

- International expansion
- US issuers
- European issuers
- Multi-currency optimization

---

## 20. Product Principles

These principles should guide every product and engineering decision.

### Portfolio First

Optimize the complete portfolio rather than individual transactions.

---

### Deterministic Before AI

Whenever a problem can be solved using deterministic logic, use deterministic logic.

Use AI only where reasoning or personalization provides additional value.

---

### Explain Everything

Every recommendation must include:

- Why it was generated.
- Supporting calculations.
- Sources.
- Confidence.
- Assumptions.

---

### Fresh Knowledge

Recommendations are only as good as the underlying knowledge.

Knowledge freshness should be treated as a first-class product capability.

---

### User Control

RewardsPilotOS assists users.

It never performs financial actions on behalf of users.

---

### Continuous Learning

Every interaction should improve future recommendations through evaluation, feedback, and product analytics while preserving user privacy.

---

## PRD Summary

The Product Requirements Document establishes the functional scope, quality standards, and implementation requirements for RewardsPilotOS.

The next sections of the specification translate these requirements into system architecture, user journeys, AI workflows, database design, APIs, and engineering implementation details.

---

# 13. User Journey

## Objective

Define the complete end-to-end user experience of RewardsPilotOS, from onboarding to receiving personalized recommendations. This document focuses on user interactions rather than system implementation.

---

# User Journey Overview

```
Sign Up
    ↓
Portfolio Setup
    ↓
Knowledge Initialization
    ↓
Dashboard
    ↓
Ask Question / Explore Recommendations
    ↓
AI Recommendation
    ↓
User Decision
    ↓
Feedback & Memory Update
    ↓
Continuous Monitoring
    ↓
Opportunity Notification
```

The journey is cyclical rather than linear. As the user's portfolio and goals evolve, RewardsPilotOS continuously improves future recommendations.

---

# Journey 1: First-Time User

## Goal

Help users set up their portfolio with minimal effort while collecting enough context to generate meaningful recommendations.

---

## Step 1: Account Creation

### User Action

The user signs in using:

- Google
- Email

### System Action

Create:

- User Profile
- Empty Portfolio
- Default Preferences

---

## Step 2: Portfolio Setup

The user adds:

- Credit Cards
- Reward Balances
- Airline Memberships
- Hotel Memberships

Optional:

- Annual Spend
- Travel Goals
- Preferred Airlines
- Preferred Hotels

---

## Step 3: Personalization

The system asks:

- Which airline do you fly most?
- Which hotel chains do you prefer?
- Do you prioritize travel or cashback?
- Do you usually book through SmartBuy?
- Do you want proactive recommendations?

The answers initialize long-term memory.

---

## Step 4: Dashboard

The user lands on the Portfolio Dashboard.

Displayed:

- Owned cards
- Reward balances
- Milestone progress
- Active recommendations
- Recent opportunities

---

# Journey 2: Spend Optimization

## Scenario

The user wants to buy a ₹95,000 laptop.

---

### User Action

The user asks:

> Which card should I use for this purchase?

---

### System Workflow

1. Load portfolio.
2. Retrieve current reward rules.
3. Identify eligible cards.
4. Apply Rule Engine.
5. Check SmartBuy opportunities.
6. Evaluate reward caps.
7. Consider milestones.
8. Generate recommendation.
9. Explain reasoning.

---

### Response

Recommended Strategy

Purchase Amazon vouchers through SmartBuy using HDFC Infinia.

Supporting Details

- Expected reward points
- SmartBuy multiplier
- Remaining monthly cap
- Milestone impact
- Supporting sources
- Confidence score

Alternative Strategy

Use Axis Atlas if preserving SmartBuy capacity for future travel.

---

# Journey 3: Transfer Planning

## Scenario

The user plans a trip to Japan.

---

### User Action

The user asks:

> What's the best use of my reward points?

---

### System Workflow

Load:

- Reward balances
- Travel goals
- Preferred airlines
- Preferred hotels

↓

Retrieve:

- Transfer ratios
- Active promotions
- Partner programs

↓

Run Graph Optimization

↓

Evaluate redemption value

↓

Generate recommendation

---

### Response

Primary Recommendation

Transfer HDFC Reward Points to Marriott Bonvoy.

Alternative Recommendation

Transfer Axis EDGE Miles to KrisFlyer for business-class flights.

Explain trade-offs between both options.

---

# Journey 4: Benefit Discovery

## Scenario

The user opens the dashboard.

---

### System Analysis

The Opportunity Engine detects:

- Lounge access unused
- Complimentary hotel stay available
- Dining benefit unused
- Annual milestone almost complete

---

### Dashboard

Highlights:

"You're missing approximately ₹12,000 worth of annual benefits."

---

### User Action

View Details

↓

Understand eligibility

↓

Redeem benefits

---

# Journey 5: Continuous Monitoring

The system continuously monitors:

- Reward rule changes
- Promotions
- Transfer bonuses
- Point expiry
- Benefit utilization

---

### Example

A new Marriott transfer bonus launches.

↓

Knowledge Platform detects the update.

↓

Rule Engine validates applicability.

↓

Opportunity Engine identifies affected users.

↓

Recommendation generated.

↓

Notification delivered.

---

### User Notification

Transfer your HDFC Reward Points to Marriott before 31 August to receive a 30% transfer bonus.

Confidence

High

Sources

Official Marriott Promotion

Official HDFC Rewards Documentation

---

# Journey 6: Learning From Feedback

## Scenario

The user ignores several airline recommendations.

---

### System Learning

Long-term memory updates:

Preferred redemption style

↓

Hotel-focused traveler

↓

Reduce airline recommendations

↓

Increase hotel recommendations

---

No business rules are modified.

Only personalization changes.

---

# Empty State Experience

## New User

Portfolio Empty

Display:

Add your first credit card to receive personalized recommendations.

---

## No Reward Balances

Display:

Enter your current reward balances for more accurate recommendations.

---

## No Travel Goals

Display:

Tell us about your travel goals so we can optimize future recommendations.

---

# Error Journey

## Scenario

Knowledge Platform unavailable.

Instead of:

"Recommendation failed."

Display:

"We couldn't verify the latest reward rules. This recommendation uses information last verified 14 hours ago."

---

# Journey Principles

Every journey should satisfy five principles.

## Personalized

Recommendations should use the user's portfolio and preferences.

---

## Explainable

Every recommendation should explain:

- Why
- How
- Supporting evidence

---

## Proactive

The product should surface opportunities without waiting for user queries.

---

## Trustworthy

Always disclose assumptions, confidence, and knowledge freshness.

---

## Low Friction

Users should reach a recommendation in as few steps as possible.

---

# 14. Decision Moments

## Overview

RewardsPilotOS is designed around high-value financial decisions rather than application screens.

Users do not open the application simply to browse information. They seek guidance at specific moments when making decisions that affect the value they receive from their credit cards.

The system continuously identifies these decision moments and provides personalized recommendations supported by deterministic calculations, graph optimization, and evidence-backed AI reasoning.

---

# Decision Moment 1: Before Making a Purchase

## User Question

Which card should I use?

---

## Typical Examples

- Buying a ₹1,20,000 laptop
- Paying insurance
- Booking flights
- Paying school fees
- Dining
- Grocery shopping
- Fuel
- Utility bills
- Online shopping
- Buying SmartBuy vouchers

---

## Inputs

Purchase amount

Merchant

Category

Current portfolio

Reward balances

Monthly spend

Reward caps

Current promotions

Travel goals

---

## AI Decision

Determine:

- Best card
- Best payment strategy
- SmartBuy opportunity
- Voucher opportunity
- Milestone impact
- Opportunity cost

---

## Expected Output

Recommended card

Expected rewards

Estimated monetary value

Reasoning

Alternative recommendation

Supporting citations

Confidence score

---

# Decision Moment 2: Before Booking Travel

## User Question

How should I pay for this trip?

---

## Example

Five nights in Singapore.

Business-class return flights.

---

## System Evaluation

Cash booking

↓

Reward redemption

↓

Transfer to airline

↓

Transfer to hotel

↓

Mixed redemption

↓

Best overall strategy

---

## Recommendation Includes

Transfer strategy

Expected redemption value

Estimated savings

Transfer timing

Supporting calculations

---

# Decision Moment 3: Before Transferring Reward Points

## User Question

Should I transfer my points today?

---

## System Evaluation

Transfer ratio

Transfer bonus

Historical redemption value

Upcoming travel

Point expiry

Alternative uses

---

## Recommendation

Transfer now

or

Wait

or

Use points differently

---

# Decision Moment 4: Before Paying an Annual Fee

## User Question

Should I renew this card?

---

## Inputs

Annual fee

Benefits used

Benefits remaining

Reward earnings

Projected future value

Competing cards

---

## Recommendation

Renew

Downgrade

Cancel

Replace

---

## Supporting Analysis

Annual fee

↓

Benefits received

↓

Expected future rewards

↓

Net annual value

---

# Decision Moment 5: Monthly Portfolio Review

Every month RewardsPilotOS automatically evaluates:

Reward balances

↓

Unused benefits

↓

Milestone progress

↓

Upcoming expirations

↓

Optimization opportunities

↓

Monthly portfolio report

---

## Example Insights

You used only 40% of your lounge benefits.

You are ₹18,000 away from an annual milestone.

Your Marriott balance has increased enough for a five-night stay.

A transfer bonus is available for your preferred airline.

---

# Decision Moment 6: Promotion Detected

Knowledge Platform detects:

- New SmartBuy offer
- Transfer bonus
- Merchant promotion
- Issuer campaign

↓

Opportunity Engine evaluates user impact.

↓

Recommendation generated.

↓

User notified only if expected value exceeds a configurable threshold.

---

# Decision Moment 7: Benefit Expiry

The Opportunity Engine continuously monitors:

Reward expiry

Voucher expiry

Annual benefits

Free hotel nights

Lounge access

Milestone deadlines

---

Instead of generic reminders, the system explains the financial impact.

Example

"You have ₹9,500 of benefits expiring within 21 days."

---

# Decision Moment 8: Planning a Major Goal

## Example Goals

Japan vacation

MBA travel

Honeymoon

Family vacation

Luxury hotel stay

Business-class redemption

---

## User Question

How should I optimize my spending over the next six months to achieve this goal?

---

## System Workflow

Current portfolio

↓

Current balances

↓

Expected monthly spending

↓

Future reward earnings

↓

Milestone forecasting

↓

Transfer forecasting

↓

Recommended strategy

---

## Example Output

Spend ₹35,000 per month on HDFC Infinia through SmartBuy.

Use Axis Atlas for travel spending.

Delay Marriott transfer until the expected bonus period.

Target 2.4 lakh reward points before booking.

Estimated savings: ₹1.3 lakh.

---

# Product Philosophy

RewardsPilotOS is not a dashboard for tracking rewards.

It is an intelligent decision support system that intervenes whenever a user is about to make a high-impact rewards decision.

Every recommendation should answer one question:

"What is the best decision I can make right now to maximize the long-term value of my rewards portfolio?"

---

# 15. Information Architecture

## Objective

The Information Architecture (IA) defines how information is organized, related, stored, and presented throughout RewardsPilotOS.

Rather than designing around screens, RewardsPilotOS is designed around entities and decision workflows. Every recommendation, notification, and dashboard component is derived from a shared information model.

---

# Design Principles

The information architecture follows six principles.

## Portfolio-Centric

The user's portfolio is the central entity from which all recommendations originate.

---

## Decision-Centric

Users interact with the system to make decisions, not to browse data.

---

## Explainability First

Every recommendation should expose the evidence, calculations, and reasoning behind it.

---

## Modular

Each domain (portfolio, rewards, knowledge, graph, memory) owns its own data and exposes clear interfaces.

---

## AI-Native

The architecture should support agent orchestration, tool calling, hybrid RAG, and persistent memory without requiring major redesign.

---

## Extensible

New issuers, loyalty programs, and recommendation types should be added without changing the overall architecture.

---

# Primary Information Domains

RewardsPilotOS is organized into eight primary domains.

## 1. User Domain

Contains information describing the user.

### Entities

- User Profile
- Preferences
- Travel Goals
- Notification Preferences
- AI Memory Profile

---

## 2. Portfolio Domain

Represents everything the user owns.

### Entities

- Credit Cards
- Reward Balances
- Loyalty Accounts
- Annual Fee Information
- Benefit Utilization
- Milestone Progress

---

## 3. Knowledge Domain

Represents external reward ecosystem knowledge.

### Entities

- Reward Rules
- Promotions
- Transfer Partners
- Benefit Guides
- SmartBuy Rules
- Official Documentation
- Community Insights

---

## 4. Recommendation Domain

Represents every recommendation produced by the system.

### Entities

- Recommendation
- Alternative Recommendations
- Supporting Calculations
- Confidence Score
- Supporting Sources
- Recommendation History

---

## 5. Graph Domain

Represents transfer relationships.

### Entities

- Reward Currency
- Airline Program
- Hotel Program
- Transfer Edge
- Transfer Bonus
- Redemption Opportunity

---

## 6. Memory Domain

Represents persistent personalization.

### Entities

- User Preferences
- Past Recommendations
- Accepted Recommendations
- Rejected Recommendations
- Long-Term Goals

---

## 7. Analytics Domain

Represents product telemetry.

### Entities

- User Events
- AI Events
- Recommendation Metrics
- System Metrics

---

## 8. Administration Domain

Represents operational data.

### Entities

- Crawls
- Knowledge Versions
- Rule Versions
- Evaluation Runs
- Agent Logs

---

# High-Level Entity Relationships

```
User
 │
 ├──────────────┐
 │              │
 ▼              ▼
Portfolio    Memory
 │              │
 │              ▼
 │      Recommendation Engine
 │              ▲
 ▼              │
Graph Engine    │
 │              │
 ▼              │
Knowledge Platform
 │
 ▼
Recommendations
 │
 ▼
Dashboard
```

---

# Navigation Architecture

The application navigation should expose the primary decision workflows instead of technical concepts.

## Primary Navigation

- Dashboard
- Portfolio
- Recommendations
- Benefits
- Travel Planner
- Knowledge
- History
- Settings

---

## Dashboard

Purpose

Provide a high-level overview of the user's rewards portfolio and current opportunities.

Contains

- Portfolio Summary
- Active Recommendations
- Opportunity Feed
- Reward Balances
- Milestones
- Benefit Utilization
- Recent Activity

---

## Portfolio

Purpose

Manage cards, balances, loyalty programs, and preferences.

Sections

- Cards
- Reward Balances
- Memberships
- Preferences
- Goals

---

## Recommendations

Purpose

View AI-generated recommendations and interact with the Recommendation Engine.

Sections

- Spend Optimization
- Transfer Planning
- Redemption Planning
- Card Comparison
- Renewal Decisions

---

## Benefits

Purpose

Track and maximize premium card benefits.

Sections

- Lounge Access
- Dining Benefits
- Hotel Benefits
- Golf Benefits
- Insurance
- Expiring Benefits

---

## Travel Planner

Purpose

Help users optimize rewards for future travel.

Sections

- Destination Planning
- Flight Strategy
- Hotel Strategy
- Transfer Planning
- Trip History

---

## Knowledge

Purpose

Allow users to explore the underlying rewards ecosystem.

Sections

- Reward Rules
- Promotions
- Transfer Partners
- Program Guides
- SmartBuy
- Issuer Updates

---

## History

Purpose

Provide transparency into past recommendations and user actions.

Sections

- Recommendation History
- Saved Recommendations
- Accepted Recommendations
- Feedback History

---

## Settings

Purpose

Manage account preferences and personalization.

Sections

- Profile
- Notification Preferences
- Memory Preferences
- Privacy Controls
- Connected Accounts (Future)

---

# Information Hierarchy

Priority 1

Information users need immediately.

- Best recommendation
- Reward balances
- Active opportunities
- Expiring benefits

---

Priority 2

Information supporting the recommendation.

- Reward calculations
- Alternative options
- Confidence score
- Sources

---

Priority 3

Detailed reference information.

- Full reward rules
- Documentation
- Transfer graphs
- Historical recommendations

---

# Search Architecture

Global search should support:

Natural language queries

Examples

- Which card should I use for insurance?
- Best Marriott transfer?
- SmartBuy rules
- Lounge benefits
- Marriott promotions

Search results may include:

- Recommendations
- Knowledge Articles
- Promotions
- Cards
- Benefits
- Transfer Partners

---

# AI Context Model

Every recommendation request should automatically assemble the following context before invoking the Planner Agent:

- User profile
- Portfolio
- Reward balances
- Current travel goals
- User preferences
- Relevant knowledge chunks
- Applicable reward rules
- Transfer graph results
- Active promotions
- Previous recommendations (when relevant)

This assembled context becomes the working memory for the recommendation workflow.

---

# Information Architecture Principles

Every new feature added to RewardsPilotOS should satisfy the following principles:

- Fits within an existing information domain or introduces a clearly defined new domain.
- Reuses existing entities wherever possible.
- Maintains a single source of truth for each entity.
- Supports explainable AI by preserving traceability from recommendation back to underlying data.
- Remains extensible for future issuers, loyalty programs, and recommendation types without requiring structural redesign.

---

# 16. System Architecture

## Purpose

Define the high-level architecture of RewardsPilotOS and explain how different subsystems collaborate to generate trustworthy, explainable, and personalized recommendations.

---

# Architecture Principles

The architecture follows the following principles:

- AI orchestrates rather than replaces deterministic logic.
- Reward calculations remain deterministic.
- AI is responsible for planning, reasoning, and explanation.
- Knowledge is retrieved rather than memorized.
- Every recommendation is explainable and traceable.
- Components are loosely coupled and independently deployable.
- New issuers and loyalty programs should be added without modifying the recommendation engine.

---

# Engineering Principle

Unknown is always preferred over incorrect.

Whenever official information cannot be verified:

- value = null
- confidence = 0
- status = unverified

The system never fabricates reward rules, transfer ratios, benefit values, or issuer policies.

Every recommendation must be traceable to an official or verified source.

---

# High-Level Architecture

```
                        +----------------------+
                        |      Frontend        |
                        |  Next.js + React     |
                        +----------+-----------+
                                   |
                                   |
                           REST / WebSocket
                                   |
                                   |
                        +----------v-----------+
                        |      Backend API     |
                        |      FastAPI         |
                        +----------+-----------+
                                   |
                  +----------------+----------------+
                  |                                 |
                  |                                 |
         +--------v--------+               +--------v--------+
         | Planner Agent   |               | Auth Service    |
         | (LangGraph)     |               +-----------------+
         +--------+--------+
                  |
          Tool Registry
                  |
    +------+------+------+------+------+------+
    |             |             |             |
    |             |             |             |
+---v---+   +-----v----+   +----v-----+ +-----v------+
|Rule   |   |Knowledge |   |Graph     | |Memory      |
|Engine |   |Platform  |   |Engine    | |Service     |
+---+---+   +-----+----+   +----+-----+ +-----+------+
    |               |              |              |
    |               |              |              |
    |        +------+-----+        |        +-----+------+
    |        | Hybrid RAG |        |        | PostgreSQL |
    |        +------+-----+        |        +------------+
    |               |              |
    |        +------+-----+        |
    |        | ChromaDB   |        |
    |        +------------+        |
    |                              |
    +------------------------------+
                  |
          Recommendation
                  |
             API Response
```

---

# Major Components

## Frontend

Responsibilities

- Portfolio management
- Recommendation visualization
- Dashboard
- AI chat
- Travel planner

Technology

- Next.js
- React
- TailwindCSS
- shadcn/ui

---

## Backend API

Responsibilities

- Authentication
- API gateway
- Request validation
- Session management
- Rate limiting

Technology

- FastAPI

---

## Planner Agent

Responsibilities

- Understand user intent
- Create execution plan
- Invoke tools
- Coordinate agent workflow
- Produce final recommendation

Technology

- LangGraph

---

## Tool Registry

Responsibilities

Expose deterministic capabilities to the Planner Agent.

Internal tools include:

- Portfolio Tool
- Rule Engine Tool
- Reward Calculator Tool
- Graph Search Tool
- Knowledge Search Tool
- Memory Tool
- Opportunity Engine Tool

External capabilities are accessed through MCP where appropriate.

---

## Knowledge Platform

Responsibilities

- Crawl reward programs
- Parse documents
- Store structured rules
- Maintain vector embeddings
- Track freshness
- Support hybrid retrieval

---

## Rule Engine

Responsibilities

- Reward calculations
- Spending multipliers
- SmartBuy rules
- Reward caps
- Eligibility rules

No LLM is used here.

---

## Graph Engine

Responsibilities

- Transfer optimization
- Partner discovery
- Multi-hop path search
- Redemption optimization

---

## Memory Service

Responsibilities

- User preferences
- Recommendation history
- Travel goals
- Accepted recommendations
- Episodic, semantic, and procedural memory

---

# Request Lifecycle

```
User Query

↓

Backend API

↓

Planner Agent

↓

Tool Registry

↓

Knowledge Search
Rule Engine
Graph Engine
Memory

↓

Planner Agent

↓

Recommendation

↓

Frontend
```

---

# Architectural Decisions

| Decision | Reason |
|----------|--------|
| LangGraph | Stateful multi-agent orchestration |
| FastAPI | High-performance Python backend |
| PostgreSQL | Structured application data |
| ChromaDB | Vector retrieval |
| Hybrid RAG | Fresh, citation-backed knowledge |
| Graph Engine | Transfer optimization |
| Rule Engine | Deterministic reward calculations |
| MCP | Standardized access to external capabilities |

---

# Non-Goals

The MVP will not include:

- Direct bank integrations
- Automatic statement parsing
- Payment execution
- Point transfers
- Live award inventory
- Financial advice

---

# Future Extensions

- Bank APIs
- Email ingestion
- OCR onboarding
- Flight search integrations
- Hotel search integrations
- Mobile application
- International issuers

---

# 17. Backend Architecture

## Purpose

The backend serves as the orchestration layer for RewardsPilotOS. It exposes APIs, manages user data, coordinates AI agents, executes deterministic business logic, retrieves knowledge, and returns explainable recommendations.

The architecture is designed to separate business logic, AI reasoning, and infrastructure concerns, making the system modular, scalable, and easy to extend.

---

# Technology Stack

| Layer | Technology |
|---------|------------|
| Backend Framework | FastAPI |
| Language | Python 3.12 |
| Authentication | JWT + OAuth |
| ORM | SQLAlchemy |
| Structured Database | PostgreSQL |
| Vector Database | ChromaDB |
| Cache | Redis |
| Agent Framework | LangGraph |
| Background Jobs | Celery + Redis |
| Scheduler | APScheduler |
| Object Storage | S3 / MinIO (future) |

---

# Backend Components

```
Frontend

↓

FastAPI

↓

Application Layer

↓

Business Services

↓

AI Layer

↓

Data Layer
```

---

# API Layer

Responsibilities

- Authentication
- Request validation
- Session handling
- Rate limiting
- API versioning
- Response serialization

Endpoints communicate only with application services.

No business logic exists inside controllers.

---

# Application Layer

Coordinates workflows across multiple services.

Responsibilities

- Portfolio orchestration
- Recommendation orchestration
- User management
- Notification management
- Travel planning
- Benefit tracking

---

# Business Services

Core backend services.

## Portfolio Service

Responsibilities

- Manage cards
- Reward balances
- Loyalty accounts
- Annual fee tracking
- Benefit utilization

---

## Recommendation Service

Responsibilities

- Receive recommendation requests
- Invoke Planner Agent
- Aggregate outputs
- Format responses

---

## Knowledge Platform

Responsibilities

- Store reward rules
- Store promotions
- Store transfer partners
- Manage document versions
- Support Hybrid RAG

---

## Rule Engine

Responsibilities

- Reward calculations
- Spending multipliers
- SmartBuy logic
- Monthly caps
- Annual milestones
- Eligibility rules

Pure deterministic logic.

---

## Graph Engine

Responsibilities

- Transfer optimization
- Partner graph
- Multi-hop routing
- Redemption optimization

---

## Memory Service

Responsibilities

- Episodic memory
- Semantic memory
- Procedural memory
- User preferences
- Long-term personalization

---

## Notification Service

Responsibilities

- Promotion alerts
- Expiry reminders
- Opportunity notifications
- Weekly portfolio summaries

---

# AI Layer

The AI layer is responsible for reasoning, planning, and recommendation generation.

Components

- Planner Agent
- Tool Registry
- Recommendation Agent
- Hybrid RAG
- Memory Retrieval

Deterministic calculations remain outside the LLM.

---

# Data Layer

## PostgreSQL

Stores

- Users
- Cards
- Reward balances
- Recommendations
- Preferences
- Goals
- History

---

## ChromaDB

Stores

- Reward documentation
- Benefit guides
- Transfer rules
- Promotions
- Community insights

---

## Redis

Stores

- Sessions
- Hot memory
- Cache
- Background task state

---

# Background Workers

Long-running jobs execute asynchronously.

Examples

- Crawl reward websites
- Parse documents
- Generate embeddings
- Refresh knowledge
- Detect promotions
- Send notifications
- Run evaluations

---

# Scheduler

Runs periodic jobs.

Examples

Every 6 hours

- Crawl issuer websites
- Check promotions

Daily

- Refresh embeddings
- Rebuild graph
- Detect rule changes

Weekly

- Portfolio review
- Recommendation digest

---

# Authentication Flow

```
User

↓

OAuth / Email Login

↓

JWT

↓

Protected APIs

↓

Application Services
```

---

# Service Communication

```
API

↓

Recommendation Service

↓

Planner Agent

↓

Tool Registry

↓

Business Services

↓

Database
```

---

# Error Handling

Backend services should return structured errors.

Example

```json
{
  "error": "KnowledgeUnavailable",
  "message": "Latest reward rules could not be verified.",
  "last_verified": "2026-08-14T10:30:00Z"
}
```

---

# Logging

Each request logs

- Request ID
- User ID
- Planner execution
- Tools invoked
- Latency
- Knowledge version
- Rule version
- Confidence score

---

# Design Decisions

| Decision | Reason |
|----------|--------|
| FastAPI | High-performance async framework |
| Service-oriented architecture | Separation of concerns |
| LangGraph | Stateful orchestration |
| Redis | Fast cache and session storage |
| PostgreSQL | Structured transactional data |
| ChromaDB | Semantic retrieval |
| Background workers | Non-blocking processing |

---

# Future Improvements

- Event-driven architecture
- Kafka for streaming updates
- Horizontal scaling
- Multi-region deployment
- gRPC between services
- Kubernetes deployment

---

# 18. Database Schema

## Purpose

RewardsPilotOS stores structured business data in PostgreSQL while storing semantic knowledge in ChromaDB. The database schema is designed around the core entities required for portfolio management, recommendations, personalization, and explainability.

---

# Database Architecture

```
                    PostgreSQL
---------------------------------------------------
Users
Portfolio
Cards
Reward Balances
Goals
Recommendations
History
Preferences
Notifications
Knowledge Metadata

                    +

                   ChromaDB
---------------------------------------------------
Reward Rules
Transfer Rules
Promotions
Benefit Guides
Issuer Policies
Travel Guides
Community Insights
```

---

# Core Entities

## User

Stores account information.

Fields

- user_id
- name
- email
- timezone
- created_at
- updated_at

Relationships

User

↓

Portfolio

↓

Goals

↓

Preferences

↓

Recommendations

---

## Portfolio

Represents the user's complete rewards ecosystem.

Fields

- portfolio_id
- user_id
- portfolio_name

Contains

- Cards
- Reward Balances
- Loyalty Programs

---

## Credit Card

Fields

- card_id
- issuer
- card_name
- network
- joining_date
- annual_fee
- renewal_date
- status

Examples

- HDFC Infinia
- Axis Atlas
- Amex Platinum Travel
- HSBC Premier
- SBI Cashback

---

## Reward Balance

Fields

- balance_id
- card_id
- reward_currency
- current_balance
- expiry_date
- last_updated

---

## Loyalty Program

Fields

- program_id
- program_name
- member_id
- current_balance

Examples

- Marriott Bonvoy
- Accor Live Limitless
- KrisFlyer
- Flying Blue
- Club Vistara

---

## User Goal

Fields

- goal_id
- destination
- target_date
- travel_type
- budget
- priority

Examples

Japan

Business Class

December 2027

---

## Recommendation

Fields

- recommendation_id
- user_id
- recommendation_type
- confidence
- status
- created_at

---

## Recommendation Evidence

Stores explainability.

Fields

- evidence_id
- recommendation_id
- rule_version
- knowledge_version
- graph_version
- retrieved_documents
- reasoning_summary

---

## User Preference

Fields

- preference_id
- preferred_airlines
- preferred_hotels
- prefers_cashback
- notification_frequency

---

## Notification

Fields

- notification_id
- type
- title
- priority
- delivered_at
- status

---

## Knowledge Metadata

Tracks freshness.

Fields

- source
- version
- last_verified
- crawl_timestamp
- parser_version

---

# Entity Relationships

```
User
 │
 ├────────────┐
 │            │
 ▼            ▼
Portfolio   Preferences
 │
 ├────────────┐
 │            │
 ▼            ▼
Cards      Loyalty Programs
 │            │
 ▼            ▼
Reward Balances
 │
 ▼
Recommendations
 │
 ▼
Recommendation Evidence
```

---

# ChromaDB Collections

reward_rules

Contains

- issuer reward rules
- earning rates
- exclusions

---

transfer_rules

Contains

- transfer partners
- ratios
- eligibility

---

promotions

Contains

- limited-time bonuses
- SmartBuy offers
- merchant campaigns

---

benefit_guides

Contains

- lounge access
- insurance
- golf
- concierge
- hotel benefits

---

issuer_updates

Contains

- policy changes
- devaluations
- announcements

---

community_insights

Contains

- Reddit
- FlyerTalk
- blogs

Clearly tagged with lower confidence than official sources.

---

# Design Principles

- Normalize transactional data.
- Version all knowledge.
- Never overwrite historical recommendations.
- Every recommendation must reference the knowledge version used.
- Every recommendation must reference the rule version used.
- Separate structured data from semantic knowledge.
- Maintain auditability for every recommendation.

---

# Future Tables

- Statement Import
- OCR Jobs
- Email Sync
- Flight Searches
- Hotel Searches
- Bank Integrations
- User Feedback
- Evaluation Results

---

# 19. API Design

## Purpose

The API layer exposes RewardsPilotOS capabilities to the frontend while hiding the complexity of the underlying AI agents, business services, and knowledge platform.

The APIs follow REST principles and return structured, explainable responses.

---

# API Principles

- Stateless APIs
- JWT authentication
- Versioned endpoints
- Consistent response format
- Explainable AI responses
- Idempotent updates where applicable

---

# API Architecture

```
Frontend

↓

REST API

↓

Application Services

↓

Planner Agent

↓

Business Services
```

---

# Authentication APIs

## POST /api/v1/auth/login

Purpose

Authenticate user.

---

## POST /api/v1/auth/logout

Purpose

End session.

---

## GET /api/v1/auth/me

Purpose

Return authenticated user.

---

# Portfolio APIs

## GET /api/v1/portfolio

Returns

- Cards
- Reward balances
- Loyalty accounts
- Portfolio summary

---

## POST /api/v1/portfolio/cards

Add a new card.

---

## PATCH /api/v1/portfolio/cards/{id}

Update card.

---

## DELETE /api/v1/portfolio/cards/{id}

Remove card.

---

## GET /api/v1/portfolio/balances

Returns all reward balances.

---

## PATCH /api/v1/portfolio/balances

Update reward balances.

---

# Recommendation APIs

## POST /api/v1/recommendations

Purpose

Generate a recommendation.

Example

Request

{
    "query": "Which card should I use for a ₹90,000 laptop?"
}

---

Response

{
    "recommendation": "...",
    "confidence": 0.94,
    "sources": [...],
    "alternatives": [...],
    "reasoning": "...",
    "knowledge_version": "...",
    "rule_version": "..."
}

---

## GET /api/v1/recommendations/history

Return previous recommendations.

---

## POST /api/v1/recommendations/{id}/feedback

Capture:

- Helpful
- Not Helpful
- Accepted
- Ignored

Used by Evaluation and Memory.

---

# Travel APIs

## POST /api/v1/travel/plan

Inputs

- Destination
- Dates
- Budget

Returns

Transfer strategy

Hotel recommendation

Airline recommendation

Expected redemption value

---

# Benefits APIs

## GET /api/v1/benefits

Returns

Unused benefits

Upcoming expiry

Lounge usage

Insurance

Dining

---

# Opportunity APIs

## GET /api/v1/opportunities

Returns

Current opportunities ranked by expected value.

Examples

- SmartBuy bonus
- Transfer bonus
- Merchant promotion
- Milestone opportunity

---

# Knowledge APIs

## GET /api/v1/knowledge/search

Purpose

Search reward rules.

Returns

Official documentation

Promotions

Transfer ratios

Benefit guides

---

## GET /api/v1/knowledge/sources

Returns

Knowledge version

Freshness

Last verified

Sources

---

# Notification APIs

## GET /api/v1/notifications

---

## PATCH /api/v1/notifications/{id}

Mark as read.

---

# Dashboard API

## GET /api/v1/dashboard

Returns

Portfolio summary

Reward balances

Top recommendations

Opportunities

Expiring benefits

Milestones

Recent activity

---

# Admin APIs

## POST /api/v1/admin/crawl

Trigger knowledge crawl.

---

## POST /api/v1/admin/reindex

Regenerate embeddings.

---

## POST /api/v1/admin/evaluate

Run evaluation suite.

---

# Standard Response Format

Success

{
    "success": true,
    "data": { ... },
    "metadata": {
        "timestamp": "...",
        "request_id": "...",
        "version": "v1"
    }
}

---

Failure

{
    "success": false,
    "error": {
        "code": "...",
        "message": "...",
        "details": { ... }
    }
}

---

# API Design Principles

- APIs never expose database schema.
- APIs return business objects, not internal models.
- Recommendation APIs always include citations and confidence.
- Long-running operations execute asynchronously.
- Every request includes a request ID for traceability.

---

# 20. Multi-Agent Architecture

## Purpose

RewardsPilotOS uses a multi-agent architecture to decompose complex recommendation tasks into specialized responsibilities. Instead of relying on a single LLM prompt, independent agents collaborate through LangGraph to retrieve information, execute deterministic calculations, optimize transfer paths, and generate explainable recommendations.

The architecture separates reasoning from execution, allowing the system to remain modular, observable, and extensible.

---

# Design Principles

- One agent, one responsibility.
- Deterministic calculations remain outside the LLM.
- Agents communicate through shared state.
- All capabilities are accessed through the Tool Registry.
- Every recommendation is explainable and traceable.
- Agents are stateless; user context is maintained by the Memory Service.

---

# Why Multi-Agent?

Many recommendation requests require multiple independent reasoning steps.

Example:

User

> I have HDFC Infinia and Axis Atlas. I'm planning a Japan trip in October. Should I spend through SmartBuy, transfer to Marriott, or save my points?

This requires:

- Understanding user intent
- Retrieving current reward rules
- Calculating reward earnings
- Checking reward caps
- Finding transfer paths
- Estimating redemption value
- Applying user preferences
- Comparing alternatives
- Explaining the recommendation

A single prompt becomes difficult to maintain, test, and evaluate.

---

# High-Level Architecture

```
                User Query
                     │
                     ▼
              Planner Agent
                     │
          Creates Execution Plan
                     │
                     ▼
              Tool Registry
      ┌────────┼────────┬─────────┐
      ▼        ▼        ▼         ▼
Knowledge   Rule     Graph     Memory
 Tool       Tool      Tool      Tool
      └────────┼────────┴─────────┘
               ▼
        Shared Agent State
               ▼
      Recommendation Agent
               ▼
      Explainable Response
```

---

# Shared State

LangGraph maintains shared execution state.

Example

```yaml
query:
portfolio:
preferences:
travel_goal:
knowledge:
graph_results:
rule_results:
memory:
recommendation:
confidence:
citations:
```

Each agent reads and updates only the fields it owns.

---

# Agent Responsibilities

## Planner Agent

Responsibilities

- Understand user intent
- Create execution plan
- Decide which tools to invoke
- Coordinate workflow
- Handle retries
- Assemble final context

Inputs

- User query
- Conversation context

Outputs

- Execution plan
- Tool invocation sequence

---

## Knowledge Agent

Responsibilities

- Retrieve relevant documents
- Apply Hybrid RAG
- Rank evidence
- Return citations
- Return freshness metadata

Outputs

- Retrieved knowledge
- Source citations
- Confidence

---

## Rule Agent

Responsibilities

- Execute deterministic reward calculations
- Apply earning rules
- Apply SmartBuy logic
- Apply monthly caps
- Validate eligibility

Outputs

- Reward calculations
- Eligible strategies

---

## Graph Agent

Responsibilities

- Search transfer graph
- Evaluate transfer paths
- Apply transfer bonuses
- Estimate redemption value

Outputs

- Ranked transfer options

---

## Memory Agent

Responsibilities

- Retrieve user preferences
- Retrieve historical recommendations
- Retrieve travel goals
- Update episodic memory

Outputs

- Personalized context

---

## Recommendation Agent

Responsibilities

- Combine outputs
- Compare alternatives
- Generate explanation
- Produce confidence score
- Attach citations

Outputs

- Final recommendation

---

# Agent Workflow

```
Planner Agent

↓

Knowledge Agent

↓

Rule Agent

↓

Graph Agent

↓

Memory Agent

↓

Recommendation Agent

↓

User Response
```

The Planner Agent may skip unnecessary agents depending on the request.

Example

Simple spending question

Planner

↓

Rule

↓

Recommendation

No graph search required.

---

# Dynamic Planning

The execution graph is constructed dynamically.

Example 1

"Which card should I use for dining?"

Planner

↓

Rule Agent

↓

Recommendation Agent

---

Example 2

"Should I transfer my points to Marriott?"

Planner

↓

Knowledge Agent

↓

Graph Agent

↓

Rule Agent

↓

Recommendation Agent

---

# Failure Handling

If one agent fails:

- Retry if transient.
- Skip optional steps.
- Continue when confidence remains acceptable.
- Return partial recommendations when possible.
- Never fabricate missing information.

---

# Observability

Each execution stores:

- Request ID
- Execution graph
- Agents executed
- Tool calls
- Retrieved documents
- Rule version
- Knowledge version
- Graph version
- Latency
- Confidence

---

# Design Decisions

| Decision | Reason |
|----------|--------|
| LangGraph | Stateful orchestration |
| Shared State | Loose coupling |
| Specialized Agents | Easier testing and evaluation |
| Deterministic Rule Engine | Eliminate calculation hallucinations |
| Planner-driven execution | Dynamic workflows |
| Tool Registry | Standardized capability access |

---

# Future Agents

Potential additions include:

- Promotion Monitoring Agent
- Statement Parsing Agent
- Email Agent
- Goal Planning Agent
- Forecasting Agent
- Fraud Detection Agent

---

# 21. Tool Calling Architecture

## Purpose

RewardsPilotOS separates reasoning from execution.

Agents are responsible for planning and decision-making.

Tools are responsible for deterministic execution.

This separation ensures recommendations remain reliable, explainable, and easy to extend.

---

# Design Principles

- Agents never implement business logic.
- Agents never query databases directly.
- Every capability is exposed as a tool.
- Tools are deterministic.
- Tools are independently testable.
- Tool outputs become inputs for downstream agents.

---

# Architecture

```
                 Planner Agent
                      │
                      ▼
                Tool Registry
                      │
      ┌───────────────┼────────────────┐
      │               │                │
      ▼               ▼                ▼
Knowledge Tool   Rule Tool      Graph Tool
      │               │                │
      └───────────────┼────────────────┘
                      ▼
                Shared State
                      ▼
           Recommendation Agent
```

---

# Tool Registry

The Tool Registry exposes all executable capabilities.

Each tool defines:

- Name
- Description
- Input schema
- Output schema
- Timeout
- Retry policy
- Owner

The Planner Agent selects tools dynamically based on user intent.

---

# Tool Categories

## Portfolio Tools

Responsibilities

- Retrieve portfolio
- Retrieve cards
- Retrieve balances
- Retrieve loyalty programs

Examples

- GetPortfolio
- GetCards
- GetRewardBalances
- GetTravelGoals

---

## Knowledge Tools

Responsibilities

- Search reward rules
- Retrieve promotions
- Retrieve SmartBuy rules
- Retrieve transfer ratios

Examples

- SearchKnowledge
- SearchPromotions
- SearchTransferPartners
- GetKnowledgeMetadata

---

## Rule Engine Tools

Responsibilities

- Calculate rewards
- Apply caps
- Apply milestones
- Apply eligibility

Examples

- CalculateRewards
- CalculateMilestones
- CheckEligibility
- EstimateRewardValue

---

## Graph Tools

Responsibilities

- Build transfer graph
- Find transfer paths
- Rank transfer options
- Estimate redemption value

Examples

- FindBestTransferPath
- CalculateCPP
- RankRedemptions

---

## Memory Tools

Responsibilities

- Retrieve preferences
- Retrieve goals
- Retrieve recommendation history
- Store episodic memory

Examples

- GetPreferences
- GetGoals
- SaveRecommendation
- SaveFeedback

---

## Opportunity Tools

Responsibilities

- Find active promotions
- Detect expiring benefits
- Detect reward expiry
- Generate opportunity alerts

Examples

- FindPromotions
- DetectExpiry
- FindUnusedBenefits

---

# Tool Lifecycle

```
Planner Agent

↓

Select Tool

↓

Validate Inputs

↓

Execute

↓

Validate Output

↓

Update Shared State

↓

Continue Execution
```

---

# Tool Selection

The Planner Agent chooses tools dynamically.

Example

Query

Which card should I use for a ₹70,000 laptop?

↓

Planner

↓

Portfolio Tool

↓

Rule Engine Tool

↓

Knowledge Tool

↓

Recommendation Agent

---

Travel Example

I want to visit Japan next March.

↓

Planner

↓

Portfolio Tool

↓

Knowledge Tool

↓

Graph Tool

↓

Memory Tool

↓

Recommendation Agent

---

# Tool Interface

Every tool returns:

- Status
- Result
- Confidence
- Metadata
- Execution time

Example

```json
{
  "status": "success",
  "result": { },
  "confidence": 0.96,
  "latency_ms": 128,
  "version": "2026.1"
}
```

---

# Error Handling

If a tool fails:

- Retry if transient
- Return structured error
- Skip optional tools
- Never fabricate results

Example

Knowledge Tool unavailable

↓

Use latest indexed knowledge

↓

Reduce confidence

↓

Inform Recommendation Agent

---

# Observability

Each tool execution records:

- Request ID
- Tool Name
- Agent
- Start Time
- End Time
- Duration
- Inputs
- Outputs
- Success / Failure
- Retry Count

---

# Design Decisions

| Decision | Reason |
|----------|--------|
| Tool Registry | Standardized execution |
| Deterministic tools | Eliminate hallucinations |
| Dynamic selection | Flexible workflows |
| Structured outputs | Agent interoperability |
| Independent tools | Easier testing |

---

# Future Tools

- Flight Search Tool
- Hotel Search Tool
- OCR Tool
- Email Parser Tool
- Statement Import Tool
- Currency Conversion Tool

---

# 22. MCP Architecture

## Purpose

The Model Context Protocol (MCP) provides a standardized interface for connecting RewardsPilotOS to external systems and services.

Rather than building custom integrations for every external capability, MCP enables the Planner Agent to interact with external tools through a consistent protocol while keeping the core system modular and extensible.

MCP is **not** responsible for business logic. It acts as an integration layer between RewardsPilotOS and external services.

---

# Why MCP?

RewardsPilotOS requires access to information and capabilities that exist outside the application.

Examples include:

- Live issuer websites
- Browser automation
- Travel search
- Email
- Calendar
- External databases

Without MCP, each integration would require custom implementation and maintenance.

MCP provides a common contract for these integrations.

---

# Design Goals

- Standardized external integrations
- Loose coupling between agents and services
- Reusable interfaces
- Easy addition of new integrations
- Independent deployment of external services
- Secure communication

---

# Role within the Architecture

```
                     User
                      │
                      ▼
               Planner Agent
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
 Internal Tool Calls           MCP Client
        │                           │
        ▼                           ▼
 Rule Engine                 MCP Servers
 Graph Engine                      │
 Memory                            │
 Knowledge Search                  ▼
                             External Systems
```

The Planner Agent decides whether a request should use an internal tool or an MCP server.

Routing decisions are deterministic whenever possible.

The Planner Agent prefers internal tools for business logic and computation.

MCP is only selected when external capabilities or live information are required.

---

# Internal Tools vs MCP

## Internal Tools

Internal tools execute deterministic business capabilities.

Examples

- Rule Engine
- Graph Engine
- Reward Calculator
- Knowledge Search
- Memory Service
- Portfolio Service

These are developed and maintained within RewardsPilotOS.

---

## MCP

MCP provides access to external systems.

Examples

- Browser automation
- Flight search
- Hotel search
- Email
- Calendar

These services exist outside the application.

---

# Responsibilities

MCP is responsible for

- Discovering external capabilities
- Executing external requests
- Returning structured responses
- Handling authentication
- Reporting failures

MCP does not

- Calculate rewards
- Make recommendations
- Execute business rules
- Store user memory
- Perform graph optimization

---

# MCP Client

The MCP Client acts as the communication layer between agents and external servers.

Responsibilities

- Server discovery
- Request routing
- Authentication
- Response validation
- Timeout handling
- Retry logic
- Error handling

The Planner Agent never communicates directly with external systems.

---

# Supported MCP Servers

## Browser MCP

Purpose

Retrieve live information from issuer websites.

Examples

- Updated reward rules
- Promotion pages
- Benefit guides
- Terms and conditions

---

## Playwright MCP

Purpose

Execute browser automation.

Examples

- Navigate websites
- Fill search forms
- Capture screenshots
- Extract dynamic content

---

## Email MCP (Future)

Purpose

Access user emails with permission.

Examples

- Reward statements
- Promotional emails
- Point expiry notifications

---

## Calendar MCP (Future)

Purpose

Create reminders.

Examples

- Reward expiry alerts
- Annual fee reminders
- Promotion end dates

---

## Flight Search MCP (Future)

Purpose

Retrieve flight availability.

Examples

- Award availability
- Flight pricing
- Airline schedules

---

## Hotel Search MCP (Future)

Purpose

Retrieve hotel availability.

Examples

- Marriott availability
- Hilton availability
- Cash vs points comparison

---

# MCP Request Flow

```
User Query

↓

Planner Agent

↓

Determine External Capability

↓

MCP Client

↓

MCP Server

↓

External System

↓

Structured Response

↓

Planner Agent

↓

Recommendation Agent

↓

User
```

---

# Authentication

Each MCP server manages its own authentication.

Supported methods include

- API Keys
- OAuth
- Service Tokens

Secrets are stored securely and are never exposed to the LLM.

---

# Error Handling

Possible failures include

- Network timeout
- Authentication failure
- Service unavailable
- Invalid response
- Rate limiting

The MCP Client returns structured errors to the Planner Agent.

Example

```json
{
  "status": "failed",
  "reason": "timeout",
  "retryable": true
}
```

The Planner Agent determines whether to retry, use cached information, or inform the user.

---

# Security Principles

- Least privilege access
- User consent for personal integrations
- Encrypted communication
- No credential exposure to the LLM
- Request validation
- Response validation

---

# Current MVP

Implemented

- Browser MCP
- Playwright MCP

These support

- Live rule verification
- Dynamic page extraction
- Knowledge validation

---

# Future Integrations

Potential MCP servers include

- Email
- Calendar
- Flight Search
- Hotel Search
- Maps
- Currency Exchange
- Banking APIs
- Notification Services

The architecture allows new servers to be added without modifying the Planner Agent.

---

# Design Decisions

| Decision | Reason |
|----------|--------|
| Separate MCP from Tool Calling | Clear separation between internal capabilities and external integrations |
| Planner Agent owns routing | Centralized orchestration |
| Standardized protocol | Easier extensibility |
| Structured responses | Reliable downstream processing |
| Independent MCP servers | Modular deployment |
| Secure authentication | Protect external credentials |

---

# Key Takeaways

MCP is the integration layer of RewardsPilotOS.

Internal tools perform deterministic business logic.

MCP servers provide access to external capabilities.

This separation keeps the architecture modular, scalable, secure, and easy to extend as new integrations are introduced.

---

# 23. Knowledge Platform (Overall Subsystem)

## Purpose

The Knowledge Platform is the source of truth for all reward-related knowledge used by RewardsPilotOS.

Its responsibilities are to continuously ingest information from trusted sources, normalize and version the data, monitor freshness, and provide reliable retrieval for downstream AI agents.

Unlike transactional user data stored in PostgreSQL, the Knowledge Platform manages external knowledge that changes frequently, such as reward rules, transfer partners, promotions, and redemption policies.

---

# Subsystem Decomposition

The Knowledge Platform is the overall subsystem. It is composed of four distinct responsibilities:

```
Knowledge Platform
    │
    ├── Knowledge Pipeline
    ├── Knowledge Store
    ├── Hybrid Retrieval
    └── Knowledge APIs
```

## Knowledge Pipeline

Ingestion of external knowledge: crawling trusted sources, parsing, normalization, versioning, and change detection.

Detailed in the Knowledge Pipeline chapter.

---

## Knowledge Store

Persistence of knowledge: PostgreSQL for structured facts and knowledge metadata, ChromaDB for semantic knowledge.

---

## Knowledge Retrieval

Hybrid Retrieval combining semantic search, keyword search, metadata filtering, and freshness-aware ranking.

Detailed in the Hybrid RAG Architecture chapter.

---

## Knowledge APIs

Retrieval interfaces exposed to the Tool Registry so the Planner Agent can access knowledge through internal tools.

---

# Design Goals

- Continuously updated knowledge
- Source-backed recommendations
- Explainable retrieval
- Freshness-aware architecture
- Easy onboarding of new issuers
- Independent of AI models

---

# High-Level Architecture

```
                  External Sources
                         │
      ┌──────────────────┼──────────────────┐
      │                  │                  │
      ▼                  ▼                  ▼
 Bank Websites      Airline Programs   Hotel Programs
      │                  │                  │
      └──────────────────┼──────────────────┘
                         │
                  Knowledge Pipeline
                         │
              Parsing & Normalization
                         │
      ┌──────────────────┼──────────────────┐
      │                                     │
      ▼                                     ▼
 PostgreSQL                         ChromaDB
 Structured Facts               Semantic Knowledge
      │                                     │
      └──────────────────┼──────────────────┘
                         ▼
                Knowledge Retrieval
                         │
                  Tool Registry
                         │
                  Planner Agent
```

---

# Responsibilities

The Knowledge Platform is responsible for:

- Maintaining reward rules
- Maintaining benefit information
- Maintaining transfer partners
- Tracking promotional campaigns
- Tracking issuer policy changes
- Versioning knowledge
- Monitoring freshness
- Supporting Hybrid RAG

---

# Knowledge Categories

## Credit Cards

Examples

- HDFC Infinia
- HDFC Diners Black
- Axis Atlas
- Amex Platinum Travel
- SBI Cashback
- ICICI Emeralde
- HSBC Premier

Stored Information

- Reward rates
- Milestones
- Reward caps
- Exclusions
- Annual fees
- Benefits

---

## Loyalty Programs

Examples

- Marriott Bonvoy
- Accor Live Limitless
- KrisFlyer
- Flying Blue
- Air India Maharaja Club

Stored Information

- Point valuation
- Redemption rules
- Elite benefits
- Expiry rules

---

## Transfer Partners

Stored Information

- Source program
- Destination program
- Transfer ratio
- Minimum transfer
- Processing time
- Restrictions

---

## Promotions

Stored Information

- Offer description
- Start date
- End date
- Eligibility
- Bonus percentage
- Source

---

## Benefit Guides

Examples

- Lounge access
- Golf benefits
- Insurance
- Dining offers
- Concierge
- SmartBuy

---

# Supported Sources

## Official Sources

Highest confidence.

Examples

- Issuer websites
- Terms & Conditions
- Reward catalogues
- Official announcements

---

## Trusted Community Sources

Medium confidence.

Examples

- Frequent Miler
- One Mile at a Time
- LiveFromALounge

---

## Community Discussions

Lower confidence.

Examples

- Reddit
- FlyerTalk

These are used only for supplementary context and are never treated as authoritative.

---

# Knowledge Storage

## Structured Database

Stores deterministic facts.

Examples

- Reward rates
- Transfer ratios
- Annual fee
- Reward caps

---

## Vector Database

Stores semantic knowledge.

Examples

- Benefit guides
- SmartBuy documentation
- Redemption guides
- Promotion descriptions

---

# Knowledge Versioning

Every document stores:

- Source
- Version
- Crawl timestamp
- Last verified
- Parser version
- Confidence score

This enables recommendation traceability.

---

# Freshness Strategy

Each knowledge source receives a refresh policy.

| Source | Refresh Frequency |
|---------|-------------------|
| Promotions | Every 6 hours |
| Issuer Rules | Daily |
| Transfer Partners | Daily |
| Benefit Guides | Weekly |
| Community Sources | Daily |

---

# Design Decisions

| Decision | Reason |
|----------|--------|
| PostgreSQL for structured facts | Fast deterministic queries |
| ChromaDB for semantic retrieval | Flexible knowledge search |
| Source versioning | Explainability |
| Freshness monitoring | Reduce stale recommendations |
| Separate knowledge from user data | Better maintainability |

---

# Future Improvements

- Automatic issuer change detection
- RSS monitoring
- AI-assisted document parsing
- Multilingual support
- Global issuer expansion

---

# 24. Knowledge Pipeline

## Purpose

The Knowledge Pipeline continuously discovers, validates, transforms, and indexes reward program information into the Knowledge Platform.

Its primary objective is to ensure that every recommendation is generated using accurate, explainable, and up-to-date information while minimizing manual maintenance.

---

# Design Goals

- Automated knowledge ingestion
- Freshness-aware updates
- Version-controlled knowledge
- Explainable recommendations
- Scalable source onboarding
- High-quality structured knowledge

---

# High-Level Pipeline

```
                External Sources
                       │
                       ▼
              Source Discovery
                       │
                       ▼
                 Web Crawlers
                       │
                       ▼
              Document Extraction
                       │
                       ▼
            Parsing & Normalization
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
 Structured Knowledge         Unstructured Knowledge
         │                           │
         ▼                           ▼
   PostgreSQL                 Chunk + Embed
                                     │
                                     ▼
                                ChromaDB
                                     │
                                     ▼
                          Knowledge Platform
```

---

# Pipeline Stages

## Stage 1. Source Discovery

Identify official and trusted sources for ingestion.

Examples

Official

- HDFC Bank
- Axis Bank
- American Express
- HSBC
- ICICI Bank
- SBI Cards
- Marriott Bonvoy
- Accor Live Limitless

Community

- LiveFromALounge
- Frequent Miler
- One Mile at a Time

---

## Stage 2. Crawling

Collect latest documents.

Examples

- Reward pages
- Terms & Conditions
- Promotions
- SmartBuy offers
- Transfer partner tables
- Benefit guides

Metadata captured

- URL
- Crawl timestamp
- Content hash
- Last modified
- Source

---

## Stage 3. Change Detection

Avoid unnecessary processing.

Compare

- Content hash
- Last modified timestamp
- Parsed output

If no meaningful change exists

↓

Skip ingestion.

---

## Stage 4. Parsing

Extract structured entities.

Examples

Reward Rate

```
5X points on SmartBuy Hotels
```

↓

```json
{
  "merchant":"SmartBuy Hotels",
  "multiplier":5,
  "category":"Hotels"
}
```

---

Transfer Rule

```
2 EDGE Miles = 1 Marriott Point
```

↓

```json
{
  "source":"Axis Atlas",
  "destination":"Marriott",
  "ratio":"2:1"
}
```

---

## Stage 5. Normalization

Standardize data across issuers.

Example

"HDFC SmartBuy"

"HDFC Smart Buy"

↓

"HDFC SmartBuy"

This ensures downstream consistency.

---

## Stage 6. Validation

Each parsed document is validated.

Checks

- Missing fields
- Invalid ratios
- Invalid dates
- Duplicate entries
- Parser confidence

Low-confidence documents are flagged for review.

---

## Stage 7. Storage

### Structured Data

Stored in PostgreSQL.

Examples

- Reward rates
- Transfer ratios
- Reward caps
- Annual fees
- Eligibility

---

### Semantic Knowledge

Stored in ChromaDB.

Examples

- Benefit guides
- FAQs
- Redemption tutorials
- SmartBuy documentation
- Offer descriptions

---

## Stage 8. Embedding Generation

Semantic documents are chunked and embedded.

Each chunk stores

- Source
- Chunk ID
- Embedding
- Version
- Last verified
- Confidence

These embeddings power Hybrid RAG.

---

## Stage 9. Versioning

Every update creates a new version.

Never overwrite previous knowledge.

Example

```
Rule Version

v1

↓

v2

↓

v3
```

Recommendations always reference the version used.

---

## Stage 10. Freshness Monitoring

Each source has an independent refresh schedule.

| Source | Frequency |
|----------|-----------|
| Promotions | Every 6 hours |
| SmartBuy | Every 6 hours |
| Reward Rules | Daily |
| Transfer Partners | Daily |
| Benefit Guides | Weekly |
| Community Sources | Daily |

---

# Knowledge Quality

Each document stores

- Source
- Confidence
- Version
- Freshness
- Parser Version
- Last Verified

This metadata is used during retrieval.

---

# Failure Handling

If crawling fails

- Retry automatically
- Preserve previous version
- Mark source as stale
- Reduce retrieval confidence

The system never deletes verified knowledge because of a temporary crawl failure.

---

# Pipeline Outputs

The pipeline produces

- Structured reward rules
- Parsed transfer partners
- Promotion database
- Knowledge embeddings
- Version history
- Freshness metadata

These outputs become inputs to the Knowledge Platform and Hybrid RAG.

---

# Design Decisions

| Decision | Reason |
|----------|--------|
| Incremental crawling | Reduce compute cost |
| Content hashing | Avoid unnecessary parsing |
| Separate structured and semantic storage | Better retrieval performance |
| Version everything | Explainability and auditing |
| Freshness-aware ingestion | Reliable recommendations |

---

# Future Improvements

- Event-driven ingestion
- RSS monitoring
- AI-assisted parser generation
- Automatic schema evolution
- Multi-region crawlers
- Human review dashboard

---

# 25. Hybrid RAG Architecture

## Purpose

RewardsPilotOS uses a Hybrid Retrieval-Augmented Generation (Hybrid RAG) architecture to retrieve accurate, fresh, and explainable reward program knowledge before generating recommendations.

Rather than relying on the LLM's parametric memory, every recommendation is grounded in the latest indexed knowledge with supporting citations.

The system combines structured retrieval, semantic search, keyword search, metadata filtering, and freshness-aware ranking to maximize retrieval quality.

---

# Why RAG?

Reward ecosystems change continuously.

Examples include:

- SmartBuy reward multipliers
- Monthly voucher limits
- Transfer ratios
- Limited-time transfer bonuses
- Card benefit changes
- Lounge access policies
- Reward devaluations

Training an LLM on this information would quickly become outdated.

Instead, RewardsPilotOS retrieves the latest verified information at runtime.

---

# Why Hybrid RAG?

Semantic search alone is insufficient.

Example

Query

> What is the monthly SmartBuy voucher cap for HDFC Infinia?

A purely semantic search may retrieve

- SmartBuy overview
- Reward earning guide
- Gift voucher documentation

instead of the exact rule containing the cap.

Hybrid retrieval combines multiple retrieval strategies.

---

# Retrieval Architecture

```
                User Query
                     │
                     ▼
              Query Processing
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
 Semantic Search          Keyword Search
 (Vector Search)              (BM25)
         │                       │
         └───────────┬───────────┘
                     ▼
            Metadata Filtering
                     ▼
           Freshness Re-ranking
                     ▼
            Context Assembly
                     ▼
             Planner Agent
                     ▼
        Recommendation Agent
```

---

# Retrieval Pipeline

## Step 1. Query Understanding

Planner Agent identifies

- User intent
- Relevant entities
- Required knowledge

Example

"I want to book Marriott using Axis Atlas."

Entities extracted

- Axis Atlas
- Marriott
- Transfer
- Redemption

---

## Step 2. Semantic Search

Vector search retrieves conceptually similar documents.

Best for

- Benefit explanations
- Redemption guides
- FAQs
- Travel recommendations

Database

ChromaDB

---

## Step 3. Keyword Search

Keyword search retrieves exact matches.

Best for

- Reward multipliers
- Card names
- Transfer ratios
- Merchant names
- SmartBuy
- Marriott
- Atlas

---

## Step 4. Metadata Filtering

Results are filtered using structured metadata.

Filters include

- Issuer
- Card
- Loyalty Program
- Country
- Document Type
- Version
- Last Verified

Example

Issuer = HDFC

Card = Infinia

Knowledge Type = SmartBuy

---

## Step 5. Freshness Re-ranking

Retrieved documents receive a freshness score.

Example

```
Final Score

=

Semantic Score

+

Keyword Score

+

Freshness Score

+

Source Confidence
```

Official, recently verified documents rank higher than older or community sources.

---

## Step 6. Context Assembly

Relevant chunks are combined into the final context.

Each chunk includes

- Source
- Version
- Last Verified
- Confidence
- Citation

---

## Step 7. Recommendation Generation

The LLM receives

- User query
- Retrieved knowledge
- Rule Engine output
- Graph Engine output
- Memory context

The LLM never performs reward calculations.

Its role is to reason over verified information and generate an explainable recommendation.

---

# Freshness-Aware Retrieval

Freshness is a first-class ranking signal.

Each document stores

- Last Verified
- Crawl Timestamp
- Version
- Source
- Confidence

Older documents receive lower ranking scores.

If knowledge becomes stale beyond a predefined threshold, the Planner Agent may invoke Browser MCP for live verification before responding.

---

# Citation Generation

Every recommendation includes supporting evidence.

Example

Recommendation

Use HDFC Infinia through SmartBuy.

Supporting Evidence

- HDFC SmartBuy Guide
- Last Verified: 12 Aug 2026
- Rule Version: v4.2

---

# Structured Knowledge vs Semantic Knowledge

## Structured Knowledge

Examples

- Reward rates
- Transfer ratios
- Reward caps
- Milestone thresholds

Retrieved from PostgreSQL.

---

## Semantic Knowledge

Examples

- Benefit guides
- FAQs
- Travel recommendations
- Promotion descriptions
- SmartBuy documentation

Retrieved from ChromaDB.

Both retrieval results are merged before recommendation generation.

---

# Failure Handling

If retrieval confidence is low

- Search additional documents
- Expand retrieval scope
- Lower recommendation confidence

If no reliable knowledge exists

- Inform the user
- Avoid speculative recommendations

The system never fabricates reward rules.

---

# Design Decisions

| Decision | Reason |
|----------|--------|
| Hybrid Retrieval | Higher recall and precision |
| Structured + Semantic Knowledge | Best of both retrieval approaches |
| Freshness-aware ranking | Prevent stale recommendations |
| Metadata filtering | Improve retrieval precision |
| Citation generation | Explainability |
| Browser MCP fallback | Live verification when required |

---

# Future Improvements

- Cross-encoder re-ranking
- Knowledge graph assisted retrieval
- Personalized retrieval ranking
- Multi-vector retrieval
- Automatic retrieval evaluation
- Continuous relevance tuning

---

# 26. Memory Architecture

## Purpose

RewardsPilotOS uses a layered memory architecture to personalize recommendations across sessions while maintaining a clear separation between short-term context, long-term preferences, and procedural knowledge.

Memory enables the system to learn user preferences, avoid repetitive recommendations, and provide context-aware assistance without retraining the underlying LLM.

---

# Design Principles

- Separate conversation memory from long-term memory.
- Different memory types serve different purposes.
- Memory is retrieved, not appended blindly to prompts.
- User memories remain isolated and private.
- Every memory has a lifecycle.

---

# Memory Architecture

```
                    User Interaction
                           │
                           ▼
                    Planner Agent
                           │
                    Memory Tool
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     Episodic         Semantic        Procedural
      Memory            Memory          Memory
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                   Recommendation Agent
```

---

# Memory Types

## Episodic Memory

Stores events that occurred during interactions.

Examples

- Previous recommendations
- Accepted recommendations
- Ignored recommendations
- Recent searches
- Planned trips
- Feedback

Purpose

Enable continuity across sessions.

---

## Semantic Memory

Stores long-term user information.

Examples

- Preferred airlines
- Preferred hotel chains
- Preferred redemption strategy
- Spending patterns
- Home airport
- Preferred travel class

Purpose

Personalize future recommendations.

---

## Procedural Memory

Stores system behaviour and execution rules.

Examples

- Agent workflows
- Tool selection policies
- Prompt templates
- Planning heuristics

Purpose

Maintain consistent reasoning.

---

# Memory Storage

## Hot Memory

Technology

Redis

Retention

Current session

Stores

- Active conversation
- Current execution state
- Temporary planner state

---

## Warm Memory

Technology

PostgreSQL

Stores

- User profile
- Portfolio
- Preferences
- Recommendation history
- Goals

---

## Semantic Memory

Technology

ChromaDB

Stores

- Embedded preferences
- Long-term interests
- Historical context
- User behaviour summaries

---

## Cold Storage

Technology

PostgreSQL Archive / Object Storage

Stores

- Old conversations
- Historical recommendations
- Audit logs
- Evaluation history

---

# Memory Retrieval

Memory retrieval occurs before recommendation generation.

```
User Query

↓

Planner Agent

↓

Memory Tool

↓

Retrieve Relevant Memories

↓

Update Shared State

↓

Recommendation Agent
```

Only relevant memories are injected into context.

---

# Memory Lifecycle

```
Interaction

↓

Store Event

↓

Classify Memory

↓

Persist

↓

Retrieve When Relevant

↓

Archive

↓

Expire (if applicable)
```

---

# What Gets Remembered

The system stores

- Preferred airlines
- Preferred hotels
- Favourite transfer partners
- Travel goals
- Notification preferences
- Recommendation feedback
- Accepted strategies

The system does not permanently store transient conversation context unless it improves future recommendations.

---

# Memory Update Policy

Update semantic memory when

- User explicitly changes a preference.
- Multiple interactions indicate a stable preference.
- Feedback consistently reinforces behaviour.

Update episodic memory after every completed recommendation.

---

# Memory Retrieval Strategy

Retrieve memories based on

- Semantic similarity
- User intent
- Recency
- Importance

Example

User

"I'm planning another Japan trip."

Retrieved memories

- Previous Japan itinerary
- Preferred airline (ANA)
- Preferred hotel (Marriott)
- Previous redemption strategy

---

# Privacy

Users can

- View stored memories
- Delete memories
- Reset personalization
- Export their data

Sensitive financial information is never embedded into semantic memory.

---

# Design Decisions

| Decision | Reason |
|----------|--------|
| Layered memory | Matches modern agent architectures |
| Redis hot cache | Fast session retrieval |
| PostgreSQL | Durable structured memory |
| ChromaDB | Semantic preference retrieval |
| Explicit memory retrieval | Smaller context windows |
| User-controlled memory | Privacy and transparency |

---

# Future Improvements

- Automatic memory summarization
- Memory importance scoring
- Memory decay
- Cross-device synchronization
- Shared family travel profiles
- Learning from long-term spending behaviour

---

# 27. Graph Engine

## Purpose

The Graph Engine models the relationships between credit cards, reward currencies, airline loyalty programs, hotel loyalty programs, merchants, and redemption options as a weighted graph.

Rather than relying on hardcoded transfer chains, the Graph Engine searches this network to identify the highest-value earning, transfer, and redemption strategy for a user's goal.

---

# Why a Graph?

Reward ecosystems are highly interconnected.

Example

```
HDFC Infinia Points
        │
        ▼
Marriott Bonvoy
        │
        ▼
Hotel Stay

Axis EDGE Miles
        │
        ▼
Flying Blue
        │
        ▼
Air France

Amex Membership Rewards
        │
        ▼
Singapore KrisFlyer
        │
        ▼
Business Class
```

A graph naturally represents these relationships and enables efficient path optimization.

---

# Design Goals

- Model reward ecosystems as a network.
- Support multi-hop transfer paths.
- Optimize for user-defined objectives.
- Adapt to changing transfer ratios and promotions.
- Explain every recommended path.

---

# Graph Model

## Nodes

Nodes represent entities.

Examples

### Credit Cards

- HDFC Infinia
- HDFC Diners Black
- Axis Atlas
- Amex Platinum Travel
- HSBC Premier
- SBI Cashback
- ICICI Emeralde

---

### Reward Currencies

- Reward Points
- EDGE Miles
- Membership Rewards

---

### Airlines

- Air India Maharaja Club
- Singapore KrisFlyer
- Flying Blue
- British Airways Executive Club
- Qatar Privilege Club

---

### Hotels

- Marriott Bonvoy
- Accor Live Limitless
- Hilton Honors
- IHG One Rewards

---

### Merchants

- SmartBuy
- Amazon
- Flipkart
- Swiggy
- Myntra

---

## Edges

Edges represent relationships.

Examples

- Earn rewards
- Transfer points
- Redeem points
- Bonus promotion
- Merchant multiplier

Each edge stores

- Transfer ratio
- Earning rate
- Processing time
- Eligibility
- Validity
- Source
- Last verified

---

# Edge Weights

Weights are dynamic.

Factors include

- Point value (CPP)
- Transfer bonus
- Processing delay
- User preferences
- Confidence
- Freshness

Example

```
Edge Score

=

Expected Value

×

Transfer Bonus

×

Preference Score

×

Freshness Score
```

---

# Optimization Goals

Different users optimize for different outcomes.

Supported objectives

- Maximum value
- Maximum points earned
- Lowest out-of-pocket cost
- Fastest redemption
- Preferred airline
- Preferred hotel
- Business class travel
- Cashback

The Planner Agent selects the optimization objective based on user intent.

---

# Example Workflow

User

"I want to book a Marriott stay in Tokyo."

↓

Planner Agent

↓

Graph Tool

↓

Graph Search

↓

Transfer Paths

↓

Rank Results

↓

Recommendation Agent

↓

Final Recommendation

---

# Example Transfer Search

```
HDFC Infinia

↓

SmartBuy

↓

Reward Points

↓

Marriott Bonvoy

↓

Tokyo Hotel
```

Alternative

```
Axis Atlas

↓

EDGE Miles

↓

Flying Blue

↓

Cash Equivalent
```

The Graph Engine compares all valid paths and returns the highest-ranked options.

---

# Promotions

Temporary promotions modify edge weights.

Examples

- 30% transfer bonus
- 5× SmartBuy earning
- Double hotel points

Promotions never modify the graph structure.

They temporarily adjust edge weights.

---

# Constraints

The Graph Engine considers

- Monthly reward caps
- Annual milestones
- Minimum transfer limits
- Point expiry
- Transfer processing time
- Program eligibility

Invalid paths are removed before ranking.

---

# Outputs

The Graph Engine returns

- Ranked transfer paths
- Estimated redemption value
- Effective transfer ratios
- Expected CPP
- Supporting calculations

---

# Explainability

Every recommendation includes

- Selected path
- Alternative paths
- Ranking score
- Applied promotions
- Transfer ratios
- Supporting sources

---

# Design Decisions

| Decision | Reason |
|----------|--------|
| Weighted graph | Natural representation of reward ecosystems |
| Dynamic edge weights | Supports changing promotions |
| Configurable objectives | Personalization |
| Explainable path ranking | User trust |
| Independent graph engine | Easy testing and extension |

---

# Future Improvements

- Real-time award availability
- Dynamic airline pricing
- Multi-city itinerary optimization
- Family point pooling
- Graph learning from historical user choices

---

# 28. Evaluation Framework

## Purpose

The Evaluation Framework measures the quality, reliability, and usefulness of RewardsPilotOS across every major subsystem.

Rather than evaluating only the LLM, the framework independently measures retrieval quality, rule execution, graph optimization, agent orchestration, and overall recommendation quality.

The objective is to ensure every recommendation is accurate, explainable, reproducible, and useful.

---

# Evaluation Principles

- Evaluate every subsystem independently.
- Separate deterministic evaluation from LLM evaluation.
- Measure product quality, not just model quality.
- Maintain reproducible evaluation datasets.
- Continuously monitor production performance.

---

# Evaluation Architecture

```
                Test Dataset
                      │
                      ▼
              Planner Agent
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Knowledge      Rule Engine   Graph Engine
    Retrieval
        │             │             │
        └─────────────┼─────────────┘
                      ▼
            Recommendation Agent
                      │
                      ▼
             Evaluation Metrics
```

---

# Evaluation Layers

## Layer 1. Knowledge Platform

Measures knowledge quality.

Metrics

- Crawl Success Rate
- Parser Accuracy
- Duplicate Detection Rate
- Freshness
- Source Coverage

---

## Layer 2. Hybrid RAG

Measures retrieval quality.

Metrics

- Precision@K
- Recall@K
- MRR (Mean Reciprocal Rank)
- NDCG
- Citation Accuracy
- Retrieval Latency

Example

Query

"What is the SmartBuy voucher cap?"

Expected

Correct SmartBuy rule retrieved within Top 3.

---

## Layer 3. Rule Engine

Measures deterministic correctness.

Metrics

- Rule Accuracy
- Calculation Accuracy
- Rule Version Consistency
- Boundary Test Pass Rate

Target

100% deterministic correctness.

---

## Layer 4. Graph Engine

Measures optimization quality.

Metrics

- Optimal Path Accuracy
- Average CPP Improvement
- Transfer Recommendation Accuracy
- Graph Search Latency

Example

Known optimal transfer path

↓

Engine recommendation

↓

Match

---

## Layer 5. Multi-Agent System

Measures orchestration quality.

Metrics

- Task Completion Rate
- Correct Tool Selection
- Agent Success Rate
- Average Execution Time
- Retry Rate

---

## Layer 6. Recommendation Quality

Measures end-user usefulness.

Metrics

- Recommendation Accuracy
- Recommendation Acceptance Rate
- Alternative Quality
- Explanation Quality
- Citation Completeness

---

# End-to-End Product Metrics

## Recommendation Accuracy

Did the system recommend the best strategy?

Target

>95%

---

## Lifetime Value Improvement

Average increase in reward value compared to a baseline strategy.

Example

User uses any card

↓

₹12,000 value

RewardsPilotOS

↓

₹15,400 value

Improvement

+28%

---

## Opportunity Capture Rate

Percentage of valuable promotions successfully identified.

Target

>90%

---

## User Satisfaction

Measured using

- Thumbs Up
- Accepted Recommendation
- Saved Recommendation
- Followed Recommendation

---

## Response Time

Measure

Time from user request to final recommendation.

Target

<3 seconds for cached knowledge.

---

## Freshness

Percentage of recommendations generated using verified knowledge.

Target

>95%

---

# Offline Evaluation Dataset

Maintain benchmark scenarios.

Examples

- Dining spend
- Flight booking
- Marriott redemption
- SmartBuy purchase
- Annual fee renewal
- Transfer bonus
- Cashback comparison
- Japan trip planning

Each scenario contains

- User portfolio
- User goal
- Expected recommendation
- Expected reasoning
- Expected citations

---

# Online Evaluation

Monitor production metrics.

Examples

- Recommendation acceptance
- User feedback
- Failed retrievals
- Low-confidence responses
- Missing citations

---

# Regression Testing

Run automatically after

- Rule updates
- Knowledge updates
- Graph updates
- Agent changes
- Prompt changes

No deployment occurs if benchmark performance decreases beyond defined thresholds.

---

# Human Evaluation

Evaluate

- Helpfulness
- Clarity
- Explainability
- Trustworthiness

Scale

1–5

---

# Evaluation Dashboard

Track

- Knowledge freshness
- Retrieval accuracy
- Agent latency
- Tool failures
- Rule accuracy
- Recommendation accuracy
- User acceptance rate

---

# Design Decisions

| Decision | Reason |
|----------|--------|
| Multi-layer evaluation | Isolate failures |
| Offline benchmark suite | Repeatable testing |
| Online monitoring | Production quality |
| Deterministic rule validation | 100% correctness |
| Recommendation acceptance | Real product metric |
| Regression testing | Prevent quality degradation |

---

# Future Improvements

- LLM-as-a-Judge for explanation quality
- Automatic retrieval benchmarking
- Continuous evaluation pipeline
- A/B testing of recommendation strategies
- Reinforcement learning from user feedback

---

would add one final metric that's very PM-oriented:

Metric	                  Why it matters
Estimated Value Created (₹)	Shows the business impact of the product

For example:

Rewards earned
Rewards saved from expiry
Extra redemption value unlocked
Annual fee offset through benefits

This becomes your North Star Metric in interviews because it directly ties the product to user value.

---

# 29. Deployment Architecture

## Purpose

The Deployment Architecture describes how RewardsPilotOS is deployed, monitored, scaled, and maintained in a production environment.

The architecture prioritizes modularity, observability, security, and scalability while remaining simple enough for an MVP and extensible for future growth.

---

# Deployment Goals

- Modular services
- Independent scaling
- High availability
- Secure infrastructure
- Comprehensive observability
- Automated deployments

---

# High-Level Architecture

```
                    Internet
                        │
                        ▼
                  Frontend (Next.js)
                        │
                  REST API Gateway
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
   Backend API     Agent Service   Knowledge Pipeline
          │             │             │
          ├─────────────┼─────────────┤
          ▼             ▼             ▼
     PostgreSQL     ChromaDB      Redis
          │
          ▼
 Object Storage (logs/backups)
```

---

# Core Services

## Frontend

Technology

- Next.js
- React
- TypeScript
- Tailwind CSS

Responsibilities

- Dashboard
- Portfolio management
- Recommendations
- User authentication

---

## Backend API

Technology

- FastAPI

Responsibilities

- Authentication
- Portfolio APIs
- Recommendation APIs
- Business services

---

## Agent Service

Technology

- LangGraph
- OpenAI / Anthropic

Responsibilities

- Planning
- Agent orchestration
- Tool execution
- Recommendation generation

---

## Knowledge Pipeline

Responsibilities

- Crawling
- Parsing
- Embedding generation
- Knowledge updates

Runs asynchronously on scheduled jobs.

---

# Data Layer

## PostgreSQL

Stores

- Users
- Portfolio
- Reward balances
- Preferences
- Recommendations
- Rule metadata

---

## ChromaDB

Stores

- Embeddings
- Knowledge chunks
- Benefit guides
- Reward documentation

---

## Redis

Stores

- Session state
- Short-term memory
- API cache
- Rate limiting

---

# Background Jobs

Examples

- Knowledge crawling
- Embedding generation
- Promotion refresh
- Rule synchronization
- Notification delivery

---

# Security

Authentication

- JWT

Authorization

- Role-based access control

Encryption

- HTTPS
- Encrypted secrets
- Encrypted database connections

Sensitive data

- Never sent to third-party MCP servers unless required
- Never embedded into vector storage

---

# Monitoring

Track

- API latency
- Agent latency
- Tool failures
- MCP failures
- Crawl success rate
- Retrieval latency
- Database performance
- Cache hit rate

---

# Logging

Every request stores

- Request ID
- User ID
- Agent execution path
- Tool calls
- MCP calls
- Latency
- Errors

Logs support debugging and evaluation.

---

# CI/CD Pipeline

```
Developer

↓

GitHub

↓

GitHub Actions

↓

Tests

↓

Build

↓

Deploy

↓

Health Checks
```

Deployment proceeds only if automated tests pass.

---

# Scaling Strategy

Scale independently

- Backend API
- Agent Service
- Knowledge Pipeline
- Vector Database

This prevents heavy crawling jobs from impacting user-facing requests.

---

# Backup Strategy

Daily

- PostgreSQL backup
- ChromaDB backup

Weekly

- Full knowledge snapshot

Monthly

- Archive logs

---

# MVP Deployment

Frontend

- Vercel

Backend

- Railway / Render

Database

- Neon PostgreSQL

Vector Database

- ChromaDB

Object Storage

- Cloudflare R2 or AWS S3

This minimizes operational complexity while supporting portfolio-scale usage.

---

# Production Deployment

Frontend

- Vercel

Backend

- Kubernetes

Databases

- Managed PostgreSQL
- Managed Vector Database

Caching

- Redis Cluster

Monitoring

- Grafana
- Prometheus

Secrets

- Cloud Secret Manager

---

# Design Decisions

| Decision | Reason |
|----------|--------|
| Service-oriented architecture | Independent scaling |
| FastAPI | Lightweight and performant |
| LangGraph service | Decoupled orchestration |
| Scheduled knowledge pipeline | Fresh data without blocking users |
| Managed databases | Reduced operational overhead |
| CI/CD with automated tests | Safe deployments |

---

# Future Improvements

- Multi-region deployment
- Blue-green deployments
- Canary releases
- Auto-scaling workers
- Event-driven knowledge pipeline
- Disaster recovery automation

---

# 30. Engineering Decisions

## Purpose

This chapter documents the major architectural and engineering decisions made during the design of RewardsPilotOS.

For each decision, the rationale, alternatives considered, and trade-offs are recorded. This improves maintainability, onboarding, and provides context for future architectural evolution.

---

# Decision Framework

Every major decision is documented using the following format:

- Problem
- Options Considered
- Selected Solution
- Why It Was Chosen
- Trade-offs
- Future Considerations

---

# Decision 1

## Multi-Agent Architecture

### Problem

Recommendation generation requires planning, retrieval, optimization, calculation, and explanation.

A single LLM prompt becomes difficult to maintain and evaluate.

### Options Considered

- Single Agent
- Multi-Agent

### Selected

Multi-Agent (LangGraph)

### Why

- Clear separation of responsibilities
- Easier testing
- Modular architecture
- Dynamic workflows
- Better observability

### Trade-offs

- Higher orchestration complexity
- Slightly higher latency

---

# Decision 2

## LangGraph

### Problem

The system requires stateful workflows and dynamic execution paths.

### Options

- LangChain
- LangGraph
- Custom Orchestrator

### Selected

LangGraph

### Why

- Stateful execution
- Conditional routing
- Retry support
- Shared state
- Production-ready orchestration

### Trade-offs

- Learning curve
- More components than simple chains

---

# Decision 3

## Tool Calling

### Problem

Business logic should not reside inside prompts.

### Options

- LLM-only
- Tool Calling

### Selected

Tool Calling

### Why

- Deterministic execution
- Better reliability
- Easier testing
- Lower hallucination risk

### Trade-offs

- Additional implementation effort

---

# Decision 4

## MCP

### Problem

External integrations should not require custom connectors.

### Options

- Custom APIs
- MCP

### Selected

MCP

### Why

- Standard interface
- Future extensibility
- Cleaner architecture
- Loose coupling

### Trade-offs

- Ecosystem still evolving

---

# Decision 5

## Hybrid RAG

### Problem

Semantic retrieval alone cannot reliably retrieve exact reward rules.

### Options

- Vector Search
- Keyword Search
- Hybrid Retrieval

### Selected

Hybrid RAG

### Why

- Higher precision
- Better recall
- Freshness-aware retrieval
- Citation support

### Trade-offs

- Slightly higher retrieval latency

---

# Decision 6

## PostgreSQL + ChromaDB

### Problem

Structured and semantic knowledge have different access patterns.

### Options

- PostgreSQL only
- Vector DB only
- Hybrid Storage

### Selected

Hybrid Storage

### Why

PostgreSQL

- Structured queries
- Transactions
- Relationships

ChromaDB

- Semantic search
- Embeddings
- Flexible retrieval

### Trade-offs

- Two storage systems to maintain

---

# Decision 7

## Rule Engine

### Problem

Reward calculations must be correct.

### Options

- LLM Calculations
- Deterministic Rule Engine

### Selected

Rule Engine

### Why

- 100% reproducible
- Independently testable
- Version controlled

### Trade-offs

- Requires rule maintenance

---

# Decision 8

## Graph Engine

### Problem

Reward transfers form a network rather than simple lookups.

### Options

- Hardcoded Rules
- Decision Trees
- Graph

### Selected

Weighted Graph

### Why

- Natural representation
- Path optimization
- Supports multi-hop transfers
- Easy to extend

### Trade-offs

- More complex implementation

---

# Decision 9

## Memory Architecture

### Problem

Recommendations should improve across sessions.

### Options

- Stateless
- Conversation History
- Layered Memory

### Selected

Layered Memory

### Why

- Better personalization
- Smaller prompts
- Clear separation of memory types

### Trade-offs

- More infrastructure

---

# Decision 10

## Knowledge Pipeline

### Problem

Reward information changes frequently.

### Options

- Manual updates
- Automated pipeline

### Selected

Automated pipeline

### Why

- Fresh knowledge
- Lower maintenance
- Versioning
- Continuous updates

### Trade-offs

- More moving parts

---

# Decision 11

## Evaluation Framework

### Problem

LLM quality alone does not measure system quality.

### Selected

Layered evaluation.

### Why

Each subsystem can fail independently.

Evaluating retrieval, graph optimization, rule execution, and recommendations separately makes failures easier to identify and fix.

---

# Summary

The architecture favors:

- Explainability over black-box reasoning
- Deterministic execution over hallucination
- Modularity over monolithic design
- Production readiness over rapid prototyping
- Long-term maintainability over short-term simplicity

---

# 31. Future Roadmap

## Vision

RewardsPilotOS begins as an intelligent rewards recommendation platform and evolves into a personal financial optimization operating system.

The long-term vision is to help users maximize the lifetime value of every financial product they own by continuously monitoring opportunities, optimizing decisions, and proactively recommending actions.

---
# Rule Verifier

An automated verification pipeline that extracts candidate reward values from official issuer documents, diffs them against current rule files, and generates a verification record for manual approval. Never writes to production rule files without explicit human approval. Documented in ADR-009 and BUILD_SPEC.md section 14a. Deferred past MVP; the MVP verification workflow is fully manual.



# Roadmap Principles

- Deliver measurable user value at every stage.
- Build platform capabilities before adding features.
- Prioritize automation over manual workflows.
- Expand from recommendations to autonomous assistance.
- Maintain explainability and user trust.

---

# Phase 1 — MVP (0–3 Months)

## Objective

Validate product-market fit and core recommendation quality.

### Features

- Portfolio management
- Credit card tracking
- Reward balance tracking
- Rule Engine
- Graph Engine
- Hybrid RAG
- Multi-Agent architecture
- Explainable recommendations
- Dashboard
- Knowledge pipeline
- Manual portfolio creation

### Success Metrics

- >95% recommendation accuracy
- <3 second response time
- 90% knowledge freshness
- Positive user feedback

---

# Phase 2 — Personalization (3–6 Months)

## Objective

Improve recommendation quality through personalization.

### Features

- Persistent memory
- User preferences
- Travel goals
- Spending goals
- Recommendation history
- Personalized opportunity ranking
- Intelligent notifications

### Success Metrics

- Higher recommendation acceptance
- Increased repeat usage
- Improved user satisfaction

---

# Phase 3 — Automation (6–12 Months)

## Objective

Reduce manual effort through intelligent automation.

### Features

- Email integration (MCP)
- Statement parsing
- OCR
- Automatic reward balance updates
- Automatic promotion discovery
- Calendar reminders
- Point expiry alerts

### Success Metrics

- Reduced manual data entry
- Increased portfolio completeness
- Higher engagement

---

# Phase 4 — Travel Intelligence (12–18 Months)

## Objective

Become a complete travel rewards planning platform.

### Features

- Flight search integration
- Hotel search integration
- Award availability monitoring
- Trip planner
- Multi-city optimization
- Family travel planning
- Transfer timing recommendations

### Success Metrics

- Higher travel redemption value
- Increased trip planning usage

---

# Phase 5 — Financial Optimization Platform (18–36 Months)

## Objective

Expand beyond rewards into holistic financial optimization.

### Features

- Cashback optimization
- Banking offers
- Investment-linked rewards
- Credit score insights
- Subscription optimization
- Bill payment optimization
- Tax-aware spending insights

---

# AI Roadmap

## Current

- Planner Agent
- Knowledge Agent
- Rule Agent
- Graph Agent
- Memory Agent
- Recommendation Agent

---

## Future

Additional agents may include:

- Forecasting Agent
- Promotion Monitoring Agent
- Statement Analysis Agent
- Travel Planning Agent
- Financial Health Agent

These will be introduced only when they solve a clear product problem.

---

# Platform Expansion

Potential future integrations include:

- Flight Search MCP
- Hotel Search MCP
- Email MCP
- Calendar MCP
- Maps MCP
- Currency Exchange MCP
- Banking APIs
- Open Banking platforms

---

# Geographic Expansion

### Phase 1

India

### Phase 2

United States

### Phase 3

United Kingdom

### Phase 4

Singapore

### Phase 5

Global reward ecosystem

---

# Product Evolution

```
Reward Recommendations

↓

Portfolio Intelligence

↓

Personalized Optimization

↓

Autonomous Financial Assistant

↓

Financial Operating System
```

---

# Long-Term Success Metrics

Measure success using:

- Monthly Active Users
- Recommendation Acceptance Rate
- Estimated Value Created (₹)
- Rewards Prevented from Expiring
- Redemption Value Unlocked
- User Retention
- Knowledge Freshness
- Recommendation Accuracy

---

# Risks

Potential challenges include:

- Frequent issuer policy changes
- Changing reward ecosystems
- Data quality maintenance
- Scaling knowledge ingestion
- Integration complexity
- Regulatory changes

---

# Guiding Principles

As the platform evolves:

- Deterministic calculations remain outside the LLM.
- Explainability remains mandatory.
- Users remain in control of automation.
- Privacy is prioritized over personalization.
- Every recommendation is backed by evidence.

---

# 32. Interview Guide

## Purpose

This chapter prepares the author to explain, justify, and defend the architectural decisions behind RewardsPilotOS during product management, AI engineering, and system design interviews.

Rather than memorizing the architecture, the objective is to understand the reasoning behind each decision, the trade-offs considered, and the evolution of the system.

---

# One-Minute Project Pitch

RewardsPilotOS is an AI-powered rewards optimization platform that helps users maximize the lifetime value of every credit card they own.

The platform combines deterministic business logic, graph optimization, Hybrid RAG, memory, and a multi-agent architecture to recommend the optimal earning, transfer, and redemption strategy while providing transparent explanations and supporting evidence.

Unlike traditional rewards calculators, RewardsPilotOS continuously updates its knowledge, personalizes recommendations, and adapts to changing reward ecosystems.

---

# Five-Minute Architecture Walkthrough

The architecture consists of seven major layers.

1. Frontend

Dashboard and portfolio management.

↓

2. API Layer

Authentication and business services.

↓

3. Multi-Agent Layer

Planner coordinates specialized agents.

↓

4. Internal Tool Layer

Deterministic business capabilities.

↓

5. Integration Layer (MCP)

Standardized access to external systems and live information.

↓

6. Knowledge Layer

Knowledge Platform, Hybrid RAG, Rule Engine, Graph Engine, Memory.

↓

7. Data Layer

PostgreSQL, ChromaDB, Redis.

---

# Why Multi-Agent?

Question

Why didn't you use a single LLM?

Answer

Recommendation generation involves multiple independent tasks including retrieval, calculation, optimization, personalization, and explanation.

Separating these responsibilities improves modularity, evaluation, and maintainability while allowing deterministic components to remain outside the LLM.

---

# Why LangGraph?

Question

Why LangGraph instead of LangChain?

Answer

LangGraph provides stateful orchestration, conditional execution, retries, shared state, and workflow control.

The project requires dynamic execution paths rather than simple prompt chains.

---

# Why Tool Calling?

Question

Why not let the LLM perform calculations?

Answer

Reward calculations are deterministic.

LLMs are excellent at reasoning but should not perform financial calculations where correctness is mandatory.

The Rule Engine performs calculations while the LLM explains the results.

---

# Why MCP?

Question

Why introduce MCP?

Answer

MCP standardizes access to external capabilities such as browser automation, email, and travel search.

Internal business logic continues to use native tools.

MCP reduces integration complexity without affecting core architecture.

---

# Why Hybrid RAG?

Question

Why not only use vector search?

Answer

Many reward rules require exact retrieval.

Hybrid RAG combines semantic similarity, keyword search, metadata filtering, and freshness-aware ranking to improve retrieval quality.

---

# Why PostgreSQL and ChromaDB?

Question

Why two databases?

Answer

Structured data such as portfolios, balances, and rules fit relational storage.

Semantic knowledge such as benefit guides and documentation benefits from vector search.

Each database serves a different access pattern.

---

# Why a Rule Engine?

Question

Why separate business logic?

Answer

Reward rules change frequently but remain deterministic.

A Rule Engine enables versioning, automated testing, reproducibility, and eliminates hallucinated calculations.

---

# Why a Graph Engine?

Question

Why model rewards as a graph?

Answer

Reward ecosystems naturally form networks.

Cards connect to reward currencies, which connect to airline and hotel programs through transfer relationships.

Graph algorithms efficiently identify optimal redemption paths.

---

# Why Memory?

Question

Why add memory?

Answer

Recommendations become more valuable when they incorporate long-term preferences, historical behavior, and user goals.

Layered memory improves personalization while keeping prompts concise.

---

# Biggest Technical Challenges

- Keeping reward information fresh.
- Managing frequent issuer policy changes.
- Balancing latency with retrieval quality.
- Maintaining explainability.
- Evaluating multi-agent workflows.

---

# Biggest Product Challenges

- User onboarding.
- Keeping portfolios updated.
- Building trust in recommendations.
- Demonstrating measurable value.
- Driving long-term engagement.

---

# Key Trade-offs

| Decision | Benefit | Cost |
|----------|---------|------|
| Multi-Agent | Modular | More orchestration |
| Hybrid RAG | Better retrieval | Higher complexity |
| Rule Engine | Deterministic | Rule maintenance |
| Graph Engine | Better optimization | More implementation effort |
| MCP | Standard integrations | Additional infrastructure |
| Layered Memory | Better personalization | More storage |

---

# If Given Six More Months

Priorities would include:

- Automatic statement import
- Email integration
- Live reward balance synchronization
- Award availability search
- Mobile application
- Personalized notifications
- Reinforcement learning from user feedback
- A/B testing recommendation strategies

---

# Lessons Learned

- AI systems require deterministic components.
- Knowledge freshness is as important as model quality.
- Explainability builds user trust.
- Evaluation should extend beyond the LLM.
- Architecture should optimize for maintainability, not novelty.

---

# Why This Project?

This project demonstrates product thinking, AI system design, backend engineering, data engineering, and evaluation in a single end-to-end system.

It reflects the design principles used in production AI platforms while addressing a real consumer problem with measurable value.

---

# Expected Interview Topics

Be prepared to discuss:

- Product discovery
- User personas
- Product-market fit
- System architecture
- AI architecture
- Multi-agent orchestration
- Hybrid RAG
- Memory systems
- Graph optimization
- Rule Engine design
- MCP integrations
- Deployment
- Evaluation
- Trade-offs
- Future roadmap

---

# Final Takeaway

RewardsPilotOS is not a chatbot that recommends credit cards.

It is an AI-native decision support system that combines deterministic computation, continuously updated knowledge, graph optimization, and intelligent orchestration to help users maximize the lifetime value of every credit card they own through transparent and explainable recommendations.

---

---

# Repository Plan

## Architecture Decision Records

In addition to the Engineering Decisions chapter, the repository maintains formal ADRs in docs/25_ARCHITECTURE_DECISION_RECORDS.md:

ADR-001: Why LangGraph?
ADR-002: Why Hybrid RAG?
ADR-003: Why Graph Engine?
ADR-004: Why Rule Engine?
ADR-005: Why MCP?
ADR-006: Why ChromaDB?
ADR-007: Why PostgreSQL?
ADR-008: Why Multi-Agent?
ADR-009: Manual Approval for Rule Verification (Fast-follow)

---

## Repository Structure

```
RewardsPilotOS/

README.md
LICENSE
.gitignore

MASTER_SPEC.md
BUILD_SPEC.md

docs/

00_VISION.md
01_PROBLEM_DISCOVERY.md
02_USER_RESEARCH.md
03_COMPETITOR_ANALYSIS.md
04_PRODUCT_REQUIREMENTS_DOCUMENT.md
05_USER_PERSONAS.md
06_USER_JOURNEY.md
07_INFORMATION_ARCHITECTURE.md
08_SYSTEM_ARCHITECTURE.md
09_MULTI_AGENT_ARCHITECTURE.md
10_TOOL_CALLING_ARCHITECTURE.md
11_MCP_ARCHITECTURE.md
12_KNOWLEDGE_PLATFORM.md
13_KNOWLEDGE_PIPELINE.md
14_HYBRID_RAG_ARCHITECTURE.md
15_MEMORY_ARCHITECTURE.md
16_GRAPH_ENGINE.md
17_RULE_ENGINE.md
18_DATABASE_SCHEMA.md
19_API_DESIGN.md
20_EVALUATION_FRAMEWORK.md
21_DEPLOYMENT_ARCHITECTURE.md
22_ENGINEERING_DECISIONS.md
23_FUTURE_ROADMAP.md
24_INTERVIEW_GUIDE.md
25_ARCHITECTURE_DECISION_RECORDS.md
99_IMPLEMENTATION_GUIDE.md
VERIFICATION_QUEUE.md
KNOWN_LIMITATIONS.md

backend/
frontend/
crawler/
knowledge/
agents/
graph/
rules/
memory/
evaluation/
mcp/
infra/
```

---

## Implementation Guide

docs/99_IMPLEMENTATION_GUIDE.md is the single source of truth for coding agents. It is distinct from the PRD.

It contains:

- Exact repository structure
- Folder responsibilities
- Technology stack
- Coding conventions
- API naming
- Database conventions
- LangGraph state schema
- Tool interfaces
- MCP interface contracts
- Graph model
- Rule format
- Prompt templates
- Environment variables
- Deployment commands
- Testing strategy
- Milestones
- Implementation order

It is the construction manual for the build.

---

## Verification Queue

docs/VERIFICATION_QUEUE.md tracks issuer data verification. All reward rates, caps, transfer ratios, and point values enter the system only after verification against official issuer sources. Unknown is always preferred over incorrect.

Priority 1 (MVP build scope): HDFC Infinia, Axis Atlas, Amex Platinum Travel
Priority 2: HDFC Diners Black, SBI Cashback, HSBC Live+
Priority 3: ICICI, AU, Yes Bank

One issuer is completed fully before the next begins, keeping the knowledge base internally consistent.

---

## Known Limitations

docs/KNOWN_LIMITATIONS.md documents MVP boundaries:

- Live reward balances are manually entered in MVP.
- No direct bank API integrations.
- Award seat availability is outside MVP.
- Promotion detection depends on crawl frequency.
- MCP integrations are partially stubbed.
- International issuers are not yet supported.
- Recommendation quality depends on verified issuer data.

---

# Appendix: Glossary

| Term | Definition |
|------|------------|
| Agent | An LLM-powered component responsible for reasoning and orchestration. |
| Tool | An internal deterministic capability invoked by an agent. |
| MCP | Model Context Protocol used to access external services through standardized interfaces. |
| Knowledge Platform | The subsystem responsible for ingesting, storing, retrieving, and serving external knowledge. |
| Knowledge Pipeline | The ingestion workflow for crawling, parsing, validating, chunking, and indexing documents. |
| Hybrid RAG | Retrieval strategy combining keyword search, vector search, metadata filtering, and freshness ranking. |
| Rule Engine | Deterministic execution engine for reward calculations and business rules. |
| Graph Engine | Optimization engine that models reward ecosystems as weighted graphs. |
| Opportunity Engine | Proactive engine that converts detected knowledge changes into user-facing opportunities and notifications. |
| Memory | Layered storage of episodic, semantic, and procedural information used for personalization. |
| ADR | Architecture Decision Record documenting important design choices. |


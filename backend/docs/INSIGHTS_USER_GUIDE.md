# AI Data Insights - User Guide

**Version:** 1.0  
**Last Updated:** April 7, 2026  
**For:** Operations Staff & Administrators

---

## What is the AI Data Insights Feature?

The AI Data Insights feature is your personal data assistant that lives right on your Dashboard. Instead of needing to understand complex databases or write technical queries, you can simply ask questions in plain English (or speak them out loud!) and get instant, visual answers about your tour operations.

Think of it like having a data analyst available 24/7 who can instantly tell you things like:
- "How many tours next week don't have guides assigned yet?"
- "Which guides have the highest ratings this month?"
- "What tours have the most cancellations?"

The system understands your question, looks through your operational data, and gives you back three things:
1. **A clear, written answer** in plain language
2. **A visual chart** (graph, bar chart, number display, etc.) to help you see the data
3. **Smart recommendations** on what actions you should take next

---

## How to Use It

### Step 1: Find the Feature

Log into your Dashboard as an admin. You'll see a section called **"Ask Your Data"** with an AI badge. This is where the magic happens!

### Step 2: Ask Your Question

You have two ways to ask questions:

**Option A: Type Your Question**
- Click in the text box
- Type your question naturally, like you're talking to a colleague
- Press Enter or click the "Ask" button

**Option B: Speak Your Question** (if your browser supports it)
- Click the microphone button (it looks like 🎤)
- The button will turn red and start pulsing - this means it's listening
- Speak your question clearly
- Click the microphone button again to stop recording
- Your question will be submitted automatically

### Step 3: Wait for Your Answer

You'll see a "Processing" message while the system works. This usually takes just a few seconds. The system is:
1. Understanding what you're asking
2. Looking through your database
3. Analyzing the results
4. Creating a chart and recommendations for you

### Step 4: Review Your Results

Once complete, you'll see three sections:

**The Chart** (shown first, because visuals are easy to understand)
- This appears in a blue-tinted card at the top
- The type of chart adapts to your data automatically

**The Answer** (the supporting explanation)
- A clear, 1-3 sentence explanation in a blue box
- This puts the numbers into context

**Recommended Actions** (what to do next)
- Up to 3 color-coded action cards
- Each tells you specifically what to do and why

---

## Types of Charts You Might See

The AI automatically picks the best chart type for your data. Here's what each one means:

### 1. **Big Number Display**
When you see: A large number in the center of the card  
What it means: You asked for a single count or total  
Example question: "How many guides do I have?"

### 2. **Bar Chart**
When you see: Horizontal bars of different lengths  
What it means: Comparing multiple items (tours, guides, months, etc.)  
Example question: "Which tours have the most bookings this month?"

### 3. **Line Chart**
When you see: A line going up and down over time  
What it means: A trend over days, weeks, or months  
Example question: "How have bookings changed over the last 6 months?"

### 4. **Donut Chart**
When you see: A ring with colored sections  
What it means: Parts of a whole (percentages)  
Example question: "What percentage of tours are in each language?"

### 5. **List**
When you see: A numbered list with values  
What it means: A ranking or detailed breakdown  
Example question: "Show me all unassigned schedules with their details"

### 6. **Comparison**
When you see: Two big numbers side by side with an arrow  
What it means: Comparing two specific values (like this week vs. last week)  
Example question: "Compare bookings this week to last week"

---

## Action Recommendations Explained

After every answer, you'll get smart recommendations color-coded by action type:

### 🔵 Train (Blue Badge)
**What it means:** Existing guides need additional training or certification  
**Example:** "3 guides need Coral Reef Tour certification to cover unassigned schedules"  
**What to do:** Arrange training sessions to expand your team's capabilities

### 🟣 Hire (Purple Badge)
**What it means:** You need to recruit new guides with specific skills  
**Example:** "No active guides speak Portuguese - consider hiring for this language"  
**What to do:** Start a recruitment process for guides with the needed expertise

### 🟢 Assign (Green Badge)
**What it means:** You have qualified guides available who should be assigned  
**Example:** "Sarah Johnson and Mike Chen are qualified and available for these 4 schedules"  
**What to do:** Go assign these specific guides to the waiting schedules

### 🟡 Review (Amber Badge)
**What it means:** The situation needs manual attention or investigation  
**Example:** "Check availability patterns - guides may have outdated schedules"  
**What to do:** Review the flagged area and update information as needed

---

## Smart Features That Make It Work

### Safety & Security
Every question you ask goes through a content safety check before being processed. If your question contains inappropriate content, you'll see a popup explaining this, and you can rephrase and try again. The feature is **admin-only** - regular users don't have access.

### SQL Transparency
At the bottom of every result, you can click "View SQL" to see the actual database query that was used. This is helpful if you want to verify what data was checked, or if you need to report a bug to your technical team.

### Voice Recognition
The feature uses your browser's built-in speech recognition. If your browser doesn't support it (or you're on a device without a microphone), the mic button simply won't appear - you can still type your questions!

### Data Enrichment for Unassigned Schedules
When you ask about schedules without guides, the system goes the extra mile. It doesn't just count them - it actually checks **why** each one is unassigned:
- Are there guides who could do it but just aren't assigned yet?
- Do guides need additional tour expertise?
- Is it a language mismatch?
- Is it an availability conflict?

This extra analysis is what powers those specific, actionable recommendations.

---

## Example Questions You Can Ask

### Scheduling Questions
- "How many upcoming schedules have no guide assigned?"
- "Which tours have the most unassigned schedules?"
- "Show me all schedules for next week"
- "What schedules are on Saturday?"

### Guide Questions
- "How many active guides do I have?"
- "Which guides have the highest ratings?"
- "Who are my top 5 guides by rating?"
- "Which guides can lead the Deep Dive tour?"
- "How many guides speak Spanish?"

### Booking & Revenue Questions
- "How many bookings do I have this month?"
- "Which tours have the most reservations?"
- "How many tickets were sold last week?"
- "What's my cancellation rate?"

### Language & Expertise Questions
- "Which languages do my guides speak?"
- "How many guides are qualified for Coral Reef tours?"
- "What tours have no available guides?"

### Trend Questions
- "How have bookings changed over the last 3 months?"
- "Show me guide ratings over time"
- "Compare this month's bookings to last month"

---

## Tips for Better Results

### ✅ Do:
- Ask specific questions with clear timeframes ("next week," "this month")
- Use proper tour names as they appear in your system
- Ask one question at a time
- Click "Ask another question" to start fresh with a new query

### ❌ Don't:
- Don't ask the system to make changes (it's read-only for safety)
- Don't expect it to predict the future (it analyzes current and historical data)
- Don't worry about perfect grammar - natural language works fine!

---

## Understanding the Technology (Optional Reading)

If you're curious about what's happening behind the scenes, here's a simplified explanation:

### The Two-Phase Process

**Phase 1: Question to Database Query**
Your natural language question is sent to OpenAI's GPT-4o AI model along with information about your database structure. The AI translates your question into a safe database query (called SQL) that can retrieve the information you need.

**Phase 2: Data to Insights**
The results from the database are sent back to GPT-4o, which:
- Interprets the numbers
- Writes a clear answer
- Chooses the best chart type
- Generates specific, actionable recommendations

### Safety Guardrails

Multiple layers of protection ensure the system is safe:

1. **Content Safety Screening:** Azure Content Safety checks every question before processing
2. **SQL Safety Guard:** The system only allows "read" queries - no modifications to your database
3. **Query Validation:** Generated queries are checked for dangerous keywords before execution
4. **Row Limits:** Results are capped at 100 rows to keep responses fast and manageable
5. **Admin-Only Access:** Only authenticated administrators can use this feature

### What Data Can It Access?

The AI has **read-only** access to these areas of your operational data:
- Schedules and tour assignments
- Guide information (names, ratings, expertise, languages)
- Bookings and reservations
- Tickets and visitor numbers
- Tours and tour types
- Availability patterns
- Survey responses and ratings
- Assignment history

The AI **cannot** access:
- User passwords or authentication data
- Payment information
- Personal customer data beyond basic booking details

---

## Troubleshooting

### "Content Flagged" Error
**What happened:** Your question was blocked by the content safety system  
**What to do:** Rephrase your question and try again. Avoid unusual characters or ambiguous phrasing.

### "AI service is temporarily unavailable"
**What happened:** The OpenAI service is down or unreachable  
**What to do:** Wait a few minutes and try again. If it persists, contact your system administrator.

### "Something went wrong"
**What happened:** A general error occurred (could be database, network, or processing issue)  
**What to do:** Try asking your question again in a different way. If it keeps failing, note the exact question and contact support.

### The microphone button doesn't appear
**What happened:** Your browser doesn't support voice input, or microphone permissions are blocked  
**What to do:** Use the text input instead. To enable voice: check your browser's microphone permissions in Settings.

### The result seems wrong or incomplete
**What happened:** The AI might have misunderstood your question or your data has unexpected patterns  
**What to do:** Click "View SQL" to see what query was run. Try rephrasing your question more specifically. If the SQL looks wrong, report it to your technical team with the original question.

---

## Privacy & Data Handling

### What gets sent to OpenAI?
- Your question text
- Database structure information (table and column names)
- Query results (up to 100 rows of data)

### What does NOT get sent?
- Your full database
- User passwords or sensitive credentials
- Any data you don't specifically ask about

### How long is data stored?
OpenAI may retain request data according to their data retention policies. Your system administrator can provide specific details about your organization's OpenAI agreement.

---

## Limitations & Known Constraints

### What This Feature Can Do
✅ Answer questions about current and historical data  
✅ Show trends and patterns  
✅ Compare numbers across categories or time periods  
✅ Provide actionable recommendations based on data  
✅ Handle complex multi-table questions  

### What This Feature Cannot Do
❌ Predict future outcomes or forecast  
❌ Make changes to your database  
❌ Remember previous questions (each query is independent)  
❌ Save query history for later reference (v1.0)  
❌ Export results to PDF or spreadsheet (v1.0)  
❌ Answer questions about data not in your database  

---

## Version Information

**Current Version:** 1.0  
**Released:** April 7, 2026

### What's New in Version 1.0
- Natural language query interface with voice support
- Six adaptive chart types (number, bar, line, donut, list, comparison)
- AI-generated actionable recommendations
- Four recommendation categories (Train, Hire, Assign, Review)
- Content safety moderation integration
- SQL transparency ("View SQL" toggle)
- Smart context enrichment for unassigned schedules
- Browser-native voice recognition support

### Future Enhancements Under Consideration
- Query history and saved insights
- Multi-turn conversational context
- Export to CSV/PDF
- Scheduled insight reports
- Custom alert triggers based on insights
- Guide-facing insights dashboard

---

## Getting Help

If you have questions, encounter issues, or want to suggest improvements:

1. **For usage questions:** Refer to this guide or ask your team administrator
2. **For technical issues:** Contact your IT/technical support team with:
   - The exact question you asked
   - The error message (if any)
   - A screenshot of the result
   - The SQL query (from "View SQL" if available)
3. **For feature requests:** Submit feedback through your organization's feature request process

---

## Quick Reference Card

| I want to... | I should... |
|--------------|-------------|
| Ask a question quickly | Type it and press Enter |
| Use voice input | Click the mic button, speak, then click it again |
| See another visualization | Ask a new question - the AI picks the best chart |
| Understand what data was used | Click "View SQL" at the bottom |
| Start over | Click "Ask another question" |
| Report an error | Screenshot the result + note your question |
| Check unassigned schedules | Ask "How many unassigned schedules?" for smart recommendations |

---

**Remember:** This tool is here to help you make better, faster decisions about your tour operations. Don't be afraid to experiment with different questions - you can't break anything, and the system is designed to understand natural language!

**Happy exploring! 🌊**

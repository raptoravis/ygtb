# ygtb Project Overview

## Project Description
ygtb is a multi-agent AI system designed for financial analysis, stock recommendation, and content processing. The project leverages the CrewAI framework to create collaborative AI agents that can perform complex tasks such as stock analysis, financial reporting, job application tailoring, and article style transformation.

## Core Features
- **Stock Analysis & Recommendation**: Multi-agent system that gathers real-time stock data, analyzes market trends, and generates investment reports
- **Financial Analysis**: Comprehensive financial analysis with risk assessment and trading strategy development
- **Article Style Analysis**: Tool for analyzing and transforming article writing styles using AI
- **Job Application Assistant**: System for tailoring job applications, resumes, and preparing for interviews
- **Media Processing**: Tools for processing video files (removing audio from MP4 files)
- **Web Scraping**: PowerShell scripts for batch scraping content from Toutiao

## Technologies Used
- Python 3.13+
- CrewAI framework for multi-agent collaboration
- LangChain for LLM integration
- Polygon API for stock data
- DuckDuckGo search API
- Bokeh for web-based UI (article style analyzer)
- MoviePy for video processing
- Selenium for web automation
- Dash for web applications

## Key Components

### Stock Analysis (`stock_analysis.py`)
- Fetches real-time stock prices and fundamentals
- Searches for recent news about stocks
- Uses three AI agents (Scout, Analyst, Writer) to generate investment reports
- Supports multiple LLM providers (Antigravity, Dashscope, Ollama, OpenAI)

### Financial Analysis (`financial_analysis.py`)
- Multi-agent system for financial market analysis
- Includes Data Analyst, Trading Strategy Developer, Trade Advisor, and Risk Advisor agents
- Monitors market data and develops trading strategies

### Article Style Analyzer (`article_style_analyzer.py`)
- Web-based tool for analyzing and transforming article writing styles
- Allows users to define writing styles based on reference articles
- Provides a UI for managing styles and applying them to new content
- Includes history tracking and content restoration features

### Job Application Assistant (`job_application.py`)
- Multi-agent system for tailoring job applications
- Includes Researcher, Profiler, Resume Strategist, and Interview Preparer agents
- Analyzes job postings and tailors resumes accordingly

## Configuration and Setup

### Environment Variables
The project requires several environment variables to be set, typically in a `~/.bbt/credentials.env` file:
- `POLYGON_API_KEY`: For stock data access
- `DASHSCOPE_API_KEY` / `DASHSCOPE_BASE_URL`: For Dashscope LLM API
- `ANTIGRAVITY_API_KEY` / `ANTIGRAVITY_BASE_URL`: For Antigravity LLM API
- `OPENAI_API_KEY` / `OPENAI_BASE_URL`: For OpenAI API access

### Dependencies
Dependencies are managed via `pyproject.toml` and include:
- crewai[tools] for multi-agent workflows
- polygon-api-client for stock data
- various web scraping and data processing libraries

## Running the Applications

### Stock Analysis
```bash
python stock_analysis.py -t NVDA --provider antigravity
```

### Article Style Analyzer
```bash
python article_style_analyzer.py --provider antigravity
```
Then visit http://localhost:6006/

### Other Components
Other scripts can be run directly with Python, with some requiring specific command-line arguments.

## Project Structure
- `main.py`: Basic entry point
- `stock_analysis.py`: Stock analysis and recommendation system
- `financial_analysis.py`: Financial market analysis tools
- `article_style_analyzer.py`: Article style transformation UI
- `job_application.py`: Job application assistance tools
- `utils.py`: Common utilities and LLM configuration
- `removeaudio.py`: Video processing tools
- `batch_scrape_toutiao.ps1`: PowerShell script for web scraping
- Various other specialized scripts

## Development Notes
- The project uses a multi-agent approach with CrewAI for complex tasks
- LLM provider selection is configurable (antigravity, dashscope, ollama, openai)
- The code is primarily in Chinese with some English comments
- Web-based interfaces use Bokeh for visualization
- Error handling and caching mechanisms are implemented for API calls
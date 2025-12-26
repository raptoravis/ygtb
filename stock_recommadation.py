# https://medium.com/data-science-collective/stock-recommendation-using-crewai-multi-agent-workflows-e0057eee14c2

# Warning control
import os
import warnings

from crewai import Agent, Crew, Process, Task
from crewai_tools import FileReadTool, ScrapeWebsiteTool, SerperDevTool
from langchain_openai import ChatOpenAI

from utils import get_openai_api_key, get_serper_api_key

warnings.filterwarnings("ignore")
openai_api_key = get_openai_api_key()
os.environ["OPENAI_MODEL_NAME"] = "gpt-4-turbo"  #'gpt-3.5-turbo', 'gpt-4-turbo', 'gpt-4.1'
os.environ["SERPER_API_KEY"] = get_serper_api_key()
search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

#### Input parameters ##########
# company = 'alphabet'
# company = 'intel'
company = "at&t"
################################

if company == "alphabet":
    file_path = "./data/Stocks-data - Alphabet.csv"
elif company == "intel":
    file_path = "./data/Stocks-data - Intel.csv"
elif company == "at&t":
    file_path = "./data/Stocks-data - AT&T.csv"
else:
    print("No such company")

file_read_tool = FileReadTool(file_path=file_path)
data_aggregation_agent = Agent(
    role="Data Aggregation Worker",
    goal="Read and analyze financial data from CSV file",
    backstory="""
        You collect and aggregate financial data from the provided CSV file for the monthly financial report.
        Analyze key financial metrics such as revenue growth, profit margins, cash flow, debt levels, and other relevant indicators.
        When asked for data, read from the CSV file using the provided function.
        """,
    verbose=True,
    allow_delegation=True,
    # tools = [search_tool, scrape_tool]
    tools=[file_read_tool],
)
report_generation_agent = Agent(
    role="Report Generation Worker",
    goal="Generate financial report",
    backstory="Generate a detailed financial report based on the data provided",
    verbose=True,
    allow_delegation=True,
    tools=[],
)
stock_analysis_agent = Agent(
    role="Stock Analysis Worker",
    goal="Analyze financial data to assess the company's stock investment potential",
    backstory="""
        You analyze financial data to assess the company's stock investment potential.
        Consider factors such as:
        - Revenue growth trends
        - Profitability and margins
        - Cash flow strength
        - Debt levels and financial stability
        - Market position and competitive advantages
        - Industry trends and outlook
        Provide a comprehensive analysis of whether the company is performing well financially.
    """,
    verbose=True,
    allow_delegation=True,
    # tools = [search_tool, scrape_tool]
    tools=[],
)
stock_recommendation_agent = Agent(
    role="Stock Recommendation Worker",
    goal="Provide BUY, HOLD, SELL recommendations on a stock",
    backstory="""
        You provide clear stock investment recommendations based on financial analysis.
        Your recommendation should be either:
        - "BUY" - if the company shows strong financial performance, growth potential, and positive indicators
        - "HOLD" - if the company shows mixed or neutral financial indicators
        - "SELL" - if the company shows poor financial performance or concerning indicators
        If the company is doing well, recommend BUY. Otherwise, recommend HOLD or SELL as appropriate.
        Provide your recommendation with clear reasoning based on the financial analysis.
        Include confidence level and key factors that influenced your decision.
    """,
    verbose=True,
    allow_delegation=True,
    tools=[],
)
accuracy_review_agent = Agent(
    role="Accuracy Review Worker",
    goal="Check the financial report and stock recommendation for accuracy and consistency",
    backstory="""
        You check the financial report and stock recommendation for accuracy and consistency.
        Verify that the analysis is based on sound financial principles and the data provided.
    """,
    verbose=True,
    allow_delegation=True,
    tools=[],
)
summary_generation_agent = Agent(
    role="Summary Generation Worker",
    goal="Summarize the financial report and stock recommendation for executive presentations",
    backstory="""
        You summarize the financial report and stock recommendation for executive presentations.
        Only include 2 points: 1. stock recommendation (BUY, HOLD, SELL), and 2. Reason.
    """,
    verbose=True,
    allow_delegation=True,
    tools=[],
)
# Task for Data Aggregation Agent
data_aggregation_task = Task(
    description=(
        """
        Collect and aggregate financial data from the provided CSV file for the monthly financial report.
        Analyze key financial metrics such as revenue growth, profit margins, cash flow, debt levels, and other relevant indicators.
        """
    ),
    expected_output=("Data aggregation report"),
    agent=data_aggregation_agent,
)
# Task for report_generation_agent
report_generation_task = Task(
    description=("Generate a detailed financial report based on the data provided by the data_aggregation_agent"),
    expected_output=("A detailed financial report based on the data provided"),
    agent=report_generation_agent,
)
# Task for stock_analysis_agent
stock_analysis_task = Task(
    description=(
        f"""
        Analyze financial data to assess the company's stock investment potential. The company is {company}.
        Consider factors such as:
        - Revenue growth trends
        - Profitability and margins
        - Cash flow strength
        - Debt levels and financial stability
        - Market position and competitive advantages
        - Industry trends and outlook
    """
    ),
    expected_output=("Provide a comprehensive analysis of whether the company is performing well financially."),
    agent=stock_analysis_agent,
    output_file="report.md",  # Outputs the report as a text file
)
# Task for stock_recommendation_agent
stock_recommendation_task = Task(
    description=(
        f"""
        Generate a detailed report, analyze stock, make a recommendation (BUY if company is doing well), review accuracy, and summarize for executives.
        The company is {company}.
        """
    ),
    expected_output=("Recommendation on whether to BUY, HOLD or SELL the stock"),
    agent=stock_recommendation_agent,
)
# Task for accuracy review agent
accuracy_review_task = Task(
    description=(
        """
        Conduct a comprehensive accuracy review of the financial report and stock recommendation to ensure quality and reliability. 
        You are also given the raw dataset in the form of a CSV file which contains the raw financial data of the company.
        
        Your review should include:
        1. Data Validation:
           - Verify all financial calculations and metrics are correct
           - Cross-check statistical analysis results
           - Validate technical indicator calculations
           - Ensure data consistency across different sections
        
        2. Logical Consistency:
           - Verify that conclusions align with the data presented
           - Check for contradictions between different analysis sections
           - Ensure recommendations are supported by evidence
           - Validate the reasoning chain from data to conclusions
        
        3. Completeness Assessment:
           - Verify all required analysis components are included
           - Check that key financial metrics are addressed
           - Ensure risk factors are properly identified
           - Confirm that both positive and negative indicators are considered
        
        4. Quality Standards:
           - Review clarity and readability of the report
           - Check for any misleading statements or omissions
           - Verify that disclaimers and limitations are appropriately stated
           - Ensure professional presentation standards are met
        
        5. Recommendation Validation:
           - Verify that the BUY/HOLD/SELL recommendation is justified
           - Check that confidence levels are appropriate
           - Ensure risk factors are properly weighted
           - Validate that the recommendation aligns with the analysis
        """
    ),
    expected_output=(
        """
        A comprehensive accuracy review report containing:
        1. Executive summary of findings
        2. Detailed validation results for each section
        3. Identified issues and inconsistencies (if any)
        4. Recommendations for corrections or improvements
        5. Overall quality assessment and confidence rating
        6. Final approval or revision requirements
        """
    ),
    agent=accuracy_review_agent,
    tools=[file_read_tool],
)
# Task for summary generation agent
summary_generation_task = Task(
    description=(
        """
        Summarize the financial report and stock recommendation for executive presentations.
        Only include 2 points: 1. stock recommendation (BUY, HOLD, SELL), and 2. Reason.
        """
    ),
    expected_output=(
        """
        A summary of the financial report and stock recommendation (BUY, HOLD, or SELL).
        """
    ),
    agent=summary_generation_agent,
)

# Define the crew with agents and tasks
financial_trading_crew = Crew(
    agents=[
        data_aggregation_agent,
        report_generation_agent,
        stock_analysis_agent,
        stock_recommendation_agent,
        accuracy_review_agent,
        summary_generation_agent,
    ],
    tasks=[
        data_aggregation_task,
        report_generation_task,
        stock_analysis_task,
        stock_recommendation_task,
        accuracy_review_task,
        summary_generation_task,
    ],
    manager_llm=ChatOpenAI(model=os.environ["OPENAI_MODEL_NAME"], temperature=0.7),
    process=Process.hierarchical,
    memory=True,
    verbose=True,
)
# Data for kicking off the process
inputs = {
    "company": company,
}
### this execution will take some time to run
result = financial_trading_crew.kickoff(inputs=inputs)

print(result)

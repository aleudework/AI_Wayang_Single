# Import libraries
from mcp.server.fastmcp import FastMCP
from typing import Optional
from ai_wayang_single.config.settings import MCP_CONFIG, INPUT_CONFIG, OUTPUT_CONFIG, DEBUGGER_MODEL_CONFIG
from ai_wayang_single.llm.agent_builder import Builder
from ai_wayang_single.llm.agent_debugger import Debugger
from ai_wayang_single.wayang.plan_mapper import PlanMapper
from ai_wayang_single.wayang.plan_validator import PlanValidator
from ai_wayang_single.wayang.wayang_executor import WayangExecutor
from ai_wayang_single.utils.logger import Logger
from ai_wayang_single.utils.schema_loader import SchemaLoader
from datetime import datetime
import os

# Initialize MCP-server
mcp = FastMCP(name="AI-Wayang-Simple", 
              port=MCP_CONFIG.get("port"))

# Initialize configs
config = {
    "input_config": INPUT_CONFIG,
    "output_config": OUTPUT_CONFIG
}

# Initialize agents and objects
builder_agent = Builder() # Initialize builder agent
debugger_agent = Debugger() # Initialize debugger agent
plan_mapper = PlanMapper(config=config) # Initialize mapper
plan_validator = PlanValidator() # Initialize validator
wayang_executor = WayangExecutor() # Wayang executor

# To store the last sessions output
last_session_result = "Nothing to output"

@mcp.tool()
def query_wayang(describe_wayang_plan: str, model: Optional[str] = "gpt-5-nano", reasoning: Optional[str] = "low", use_debugger: Optional[str] = "True") -> str:
    """
    Generates and execute a Wayang plan based on given query in national language.
    The query provided must be in Englis

    Args:
        describe_wayang_plan (str):
            A detailed description in English of what query or task should be executed
    
    Returns:
        Execution output from Wayang server
    
    Notes:
    - This tool builds and execute a query based on a description 
    - Runetime is typically a few minutes
    - Be as detailed in the description as possible
    """

    # Declaring variable as global
    global last_session_result

    # Sets parametre (mainly for evaluation)
    builder_agent.set_model_and_reasoning(model, reasoning)
    debugger_agent.set_model_and_reasoning(model, reasoning)

    try:
        # Set up logger 
        logger = Logger()
        logger.add_message("User query: Plan description from client LLM", describe_wayang_plan)
        logger.add_message("Architecture", {"model": model, "architecture": "Single", "debugger": use_debugger})
        
        # Initialize variables
        status_code = None # Status code from validator or Wayang server
        result = None # Variable to store output
        version = 1 # Keeping track of plan version for this session


        ### --- Generate Wayang Plan Draft --- ###

        # Generate plan
        print("[INFO] Generates raw plan")
        response = builder_agent.generate_plan(describe_wayang_plan)
        raw_plan = response.get("wayang_plan")

        # Logging
        print("[INFO] Draft generated")
        logger.add_message("Agent Usage: BuilderAgent Information", {"model": str(response["raw"].model), "usage": response["raw"].usage.model_dump()})
        logger.add_message("Agent: BuilderAgent Raw Plan", raw_plan.model_dump())


        ### --- Map Raw Plan to Executable Plan --- ###

        # Map plan
        print("[INFO] Mapping plan")
        wayang_plan = plan_mapper.plan_to_json(raw_plan)

        # Logging
        print("[INFO] Plan mapped")
        logger.add_message("Class: PlanMapper Mapped plan finalized for execution", {"version": 1, "plan": wayang_plan})


        ### --- Validate Plan --- ###

        # Logging
        print("[INFO] Validating plan")
        logger.add_message(f"Class: PlanValidator Validates Plan", "")


        # Validate plan before execution
        val_success, val_errors = plan_validator.validate_plan(wayang_plan)

        # Tell and log validation result
        if val_success:
            print("[INFO] Plan validated sucessfully")

        else:
            # Logging if validation fails
            print(f"[INFO] Plan {version} failed validation: {val_errors}")
            logger.add_message(f"Err: PlanValidator Val error. Failed validation", {"version": version, "errors": val_errors})
            status_code = 400


        ### --- Execute Plan If Validated Successfully --- ###

        if val_success:
            # Execute plan in Wayang
            print("[INFO] Plan sent to Wayang for execution")
            status_code, result = wayang_executor.execute_plan(wayang_plan)
            logger.add_message("Wayang: Wayang plan sent to Wayang", "")
            
            # Log if plan couldn't execute
            if status_code != 200:
                print(f"[INFO] Couldn't execute plan succesfully, status {status_code}")
                logger.add_message("Err: Wayang error. Plan executed unsucessful", {"status_code": status_code, "output": result})
        

        ### --- Debug Plan --- ###
        
        # Check if debugger should be used
        #use_debugger = DEBUGGER_MODEL_CONFIG.get("use_debugger")

        # Use debugger if true
        if use_debugger == "True" and status_code != 200:

            # Start logging
            print("[INFO] Using Debugger Agent to fix plan")

            # Set debugging parameters
            max_itr = int(DEBUGGER_MODEL_CONFIG.get("max_itr")) # Get max iterations for debugging
            debugger_agent.set_vesion(version) # Set version to number of plans already created this session
            debugger_agent.start_debugger() # Load debugger session 

            # Debug and execute plan up to max iterations
            for _ in range(max_itr):

                # Map and anonymize plan from executable json to raw format
                failed_plan = plan_mapper.plan_from_json(wayang_plan)
                logger.add_message("Class: PlanMapper Simplifies JSON", "")
                print(f"[INFO] PlanMapper Simplifies JSON")

                # Debug plan
                response = debugger_agent.debug_plan(describe_wayang_plan, failed_plan, wayang_errors=result, val_errors=val_errors) # Debug plan
                version = debugger_agent.get_version() # Current plan version
                raw_plan = response.get("wayang_plan") # Get only the debugged plan
                print("[INFO] Plan debugged by debugger")

                # Get current plan version
                version = debugger_agent.get_version()

                # Logging
                logger.add_message(f"Agent Usage: DebuggerAgent. Debug version {version} information", {"model": str(response["raw"].model), "usage": response["raw"].usage.model_dump()})
                logger.add_message(f"Agent: DebuggerAgent's thoughts, plan {version}", {"version": version, "thoughts": raw_plan.thoughts})
                logger.add_message(f"Agent: DebuggerAgent's plan: {version}", {"version": version, "plan": raw_plan.model_dump()})


                # Map the debugged plan to JSON-format
                wayang_plan = plan_mapper.plan_to_json(raw_plan)
                print("[INFO] Plan mapped by PlanMapper")
                logger.add_message("Class: PlanMapper Mapped Debug Plan", "")
                
                # Validate debugged plan
                val_success, val_errors = plan_validator.validate_plan(wayang_plan)

                print(f"[INFO] PlanValidator validates debugger's plan")
                logger.add_message("Class: PlanValidator Validated Debugger Plan", "")

                # If plan failed validation, continue debugging
                if not val_success:
                    # Logging failure
                    print(f"[INFO] Plan {version} failed validation: {val_errors}")
                    logger.add_message(f"Err: PlanValidator Val error. Failed validation", {"version": version, "errors": val_errors})
                    status_code = 400
                    result = None
                    continue

                print(f"[INFO] Succesfully validated and debugged plan, version {version}") # If plan validation succesfully
                
                # Execute Wayang plan
                print(f"[INFO] Plan {version} sent to Wayang for execution")
                status_code, result = wayang_executor.execute_plan(wayang_plan)
                logger.add_message("Wayang: Wayang plan sent to Wayang", "")

                # Break debugging loop if sucessfully executed
                if status_code == 200:
                    break

                # Continue debugging if execution failed
                if status_code != 200:
                    print(f"[ERROR] Couldn't execute plan version {version}, status {status_code}")
                    logger.add_message(f"Err: Wayang error. Plan version {version} executed unsucessful", {"status_code": status_code, "output": result})
                    continue
            
        # Return output when success
        if status_code == 200:
            print("[INFO] Plan succesfully executed")
            logger.add_message("Final: Sucessful. Plan executed", "Success")

            # Return result to client
            return result

        # If failed to execute plan after debugging
        if status_code != 200:
            print(f"[ERROR] Couldn't execute plan succesfully, status {status_code}")
            logger.add_message("Final: Unsucessful. Plan executed unsucessful", {"status_code": status_code, "output": result})
            
            # Return failure to client
            return "Couldn't execute wayang plan succesfully"

    except Exception as e:
        # Prints if an exception happened
        print(f"[ERROR] {e}")

        # Return error to client LLM to explain to user
        msg = f"An error occured, explain for the user: {e}"
        # Return error message to client
        return msg


@mcp.tool()
def get_wayang_result() -> str:
    """
    Get the current result from query_wayang or from the Wayang execution.

    Returns:
        The output result or output error from Wayang
    
    """

    return last_session_result

@mcp.tool()
def load_schemas() -> str:
    """
    Loads schemas with examples from database and textfiles for agents.

    Returns
        str: Informationen on number of added schemas
    """
    try:

        # Create output folder path
        base_dir = os.path.dirname(os.path.abspath(__file__)) # Path to server file
        relative_path = os.path.join(base_dir, "..", "..", "..", "data", "schemas") # Relative path to output folder
        output_folder = os.path.abspath(relative_path) # Absolute path to folder
        
        # Initialize schema loader
        schema_loader = SchemaLoader(config, output_folder)
        
        # For output messages
        msg = []

        # Load jdbc tables
        msg.append(schema_loader.get_and_save_table_schemas())

        # Load textfiles
        msg.append(schema_loader.get_and_save_textfile_schemas())

        # Returns msg as str to client
        return "\n".join(msg)

    except Exception as e:
        # Print and returns error
        print(f"[ERROR] {e}")
        return f"An error occured, error: {e}"
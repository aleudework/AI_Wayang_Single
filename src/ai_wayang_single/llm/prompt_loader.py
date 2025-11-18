from pathlib import Path
import os
import json
from typing import List, Dict
from ai_wayang_single.llm.models import WayangPlan


class PromptLoader:
    """
    Loads and prepares prompts for agents

    """
    def __init__(self, prompt_folder: str | None = None, data_folder: str | None = None):
        self.prompt_folder = Path(__file__).resolve().parent / "prompts"
        self.data_folder = Path(__file__).resolve().parent.parent.parent.parent / "data"
    
    def load_builder_system_prompt(self) -> str:
        """
        Load and prepare system prompt for Builder Agent

        Returns:
            (str): Builder's system prompt

        """

        # Get system prompt template
        system_prompt = self._read_file(self.prompt_folder, "builder_prompts/system_prompt.txt")
        
        # Get general prompt templates
        data_prompt = self.load_data_prompt()
        operator_prompt = self.load_operators()
        few_shot_prompt = self.load_few_shot_prompt()

        # Fill system prompt template
        system_prompt = system_prompt.replace("{data}", data_prompt)
        system_prompt = system_prompt.replace("{operators}", operator_prompt)
        system_prompt = system_prompt.replace("{examples}", few_shot_prompt)

        return system_prompt
    

    def load_debugger_system_prompt(self) -> str:
        """
        Load and prepare system prompt for Debugger Agent

        Returns:
            (str): Debuggers's system prompt

        """

        # Load system prompt template
        system_prompt = self._read_file(self.prompt_folder, "debugger_prompts/system_prompt.txt")

        # Load general prompt templates
        operators_prompt = self.load_operators()

        # Fill system prompt
        system_prompt = system_prompt.replace("{operators}", operators_prompt)

        # Get and return system prompt
        return system_prompt
    

    def load_debugger_prompt(self, query: str, failed_plan: WayangPlan, wayang_errors: str, val_errors: List) -> str:
        """
        Load and prepare prompt to be sent to the Debugger.
        The prompt is about fixing a failed plan

        Args:
            query (str): The original natural-language user query
            failed_plan (WayangPlan): The failed Wayang plan
            wayang_errors (str): The error provided by the Wayang server
            val_errors (List): Errors from PlanValidator if any

        Returns:
            (str): Debuggers prompt to be sent to the Debugger Agent

        """

        # Get prompt template
        prompt_template = self._read_file(self.prompt_folder, "debugger_prompts/prompt.txt")

        # Convert to correct JSON from WayangPlan model
        if hasattr(failed_plan, "model_dump"):
            failed_plan = json.dumps(failed_plan.model_dump(), indent=4)
        elif hasattr(failed_plan, "to_json"):
            failed_plan = failed_plan.to_json(indent=4)
        elif not isinstance(wayang_errors, str):
            failed_plan = json.dumps(failed_plan.__dict__, indent=4)

        # Convert to JSON
        if not isinstance(wayang_errors, str):
            wayang_errors = json.dumps(wayang_errors, indent=4)

        # Converts val error to string
        val_errors = "\n".join([f"- {str(e)}" for e in val_errors])

        # Fill template
        prompt_template = prompt_template.replace("{query}", query)
        prompt_template = prompt_template.replace("{failed_plan}", failed_plan)
        prompt_template = prompt_template.replace("{wayang_error}", wayang_errors)
        prompt_template = prompt_template.replace("{val_error}", val_errors)

        return prompt_template
    
    
    def load_debugger_answer(self, wayang_plan: WayangPlan) -> str:
        """
        Load and prepare Debugger Agents answer. It is for it to keep track of its own answers when debugging in multiple iterations

        Args:
            wayang_plan (WayangPlan): The WayangPlan fixed by the Debugger Agent in current iteration

        Returns:
            (str): The answer to be linked to the Debugger Agent's chat in current session

        """

        # Load answer template
        answer_prompt = self._read_file(self.prompt_folder, "debugger_prompts/answer.txt")

        # Load debuggers fixed plan and thoughts
        fixed_plan = json.dumps([op.model_dump() for op in wayang_plan.operations], indent=2, ensure_ascii=False)
        thoughts = wayang_plan.thoughts
        
        # Fill template
        answer_prompt = answer_prompt.replace("{fixed_plan}", fixed_plan)
        answer_prompt = answer_prompt.replace("{thoughts}", thoughts)

        # Return prompt
        return answer_prompt
    

    
    def load_data_prompt(self) -> str:
        """
        Loads data prompt with schemas in it

        Returns:
            (str): Data prompt
        
        """

        # Load data prompt template
        data_prompt = self._read_file(self.prompt_folder, "data.txt")

        # Load schemas
        schemas = self._load_schemas()

        # Format to string for prompt
        tables_str = "\n\n".join(schemas.get("tables", []))
        textfiles_str = "\n\n".join(schemas.get("text_files", []))

        # Add schemas to prompt template
        data_prompt = data_prompt.replace("{jdbc_tables}", tables_str)
        data_prompt = data_prompt.replace("{text_files}", textfiles_str)

        # Return prompt
        return data_prompt
    
    
    def load_few_shot_prompt(self) -> str:
        """
        Load few shot prompt template

        Returns:
            (str): Few shot prompt template

        """

        few_shot_folder = os.path.join(self.data_folder, "few_shot_examples")

        # Check if folder exists
        if not os.path.exists(few_shot_folder):
            raise FileNotFoundError(f"Schema folder does not exists at {few_shot_folder}")
        
        # Load few shot examples
        few_shot_examples = self._read_txt_files(few_shot_folder)

        # Load few shot prompt
        few_shot_prompt = self._read_file(self.prompt_folder, "few_shot.txt")

        # Convert examples to list
        few_shot_str = "\n\n".join(few_shot_examples)
    
        # Add examples to prompt template
        few_shot_prompt = few_shot_prompt.replace("{examples}", few_shot_str)

        # Return prompt
        return few_shot_prompt
    

    def load_operators(self) -> str:
        """
        Load operators prompt template

        Returns:
            (str): String of operations

        """

        # Return operators prompt template
        return self._read_file(self.prompt_folder, "operators.txt")

    
    def _load_schemas(self) -> Dict:
        """
        Helper function to load data schemas

        Args:


        Returns:
            (Dict): The final data prompt to be used

    """
        # Create schema folder path
        schema_folder = os.path.join(self.data_folder, "schemas")

        # Check if folder exists
        if not os.path.exists(schema_folder):
            raise FileNotFoundError(f"Schema folder does not exists at {schema_folder}")
        
        # Create table and textfile schemas
        table_folder = os.path.join(schema_folder, "tables")
        textfile_folder = os.path.join(schema_folder, "text_files")
        
        # List to store json schemas
        table_schemas = self._read_json_files(table_folder)
        textfile_schemas = self._read_json_files(textfile_folder)

        # To store json
        tables = []
        textfiles = []

        # Format tables
        for schema in table_schemas:
            formatted = json.dumps(schema, indent=3, ensure_ascii=False)
            tables.append(formatted)

        # Format textfiles
        for schema in textfile_schemas:
            formatted = json.dumps(schema, indent=3, ensure_ascii=False)
            textfiles.append(formatted)

        # Return schemas
        schemas = {
            "tables": tables,
            "text_files": textfiles
        
        }
        
        return schemas
    
    
    def _read_txt_files(self, folder: str | Path) -> List:
        """
        Helper function to take a folder and read all textfiles

        Args:
            folder (str | Path): Path of folder

        Returns:
            (List): List of all found .txt files

        """

        # List to store json
        output = []

        # Go over each .txt file
        for root, _, files in os.walk(folder):
            for file in files:
                # IF json file
                if file.endswith(".txt"):
                    # Read file and append to schemas
                    f = self._read_file(root, file)
                    output.append(f)

        return output
    
     
    def _read_json_files(self, folder: str | Path) -> List:
        """
        Helper function that take and folder and returns all json in folder and lower level folders
        
        Args:
            folder (str | Path): Path of folder

        Returns:
            (List): List of all found json

        """

        # List to store json
        output = []

        # Go over each json file
        for root, _, files in os.walk(folder):
            for file in files:
                # IF json file
                if file.endswith(".json"):
                    # Read file and append to schemas
                    json_data = self._read_file(root, file)
                    output.append(json.loads(json_data))

        return output

    
    def _read_file(self, folder: str | Path, file: str) -> str:
        """
        Helper function to open prompt template files

        Args:
            folder (str | Path): Path to folder
            file (str): Name of prompt file including extension (.txt)

        Returns:
            (str): The file

        """
        # Convert to path if str
        if isinstance(folder, str):
            folder = Path(folder)

        # Build file path
        file_path = folder / file

        # Open file if exists
        if not file_path.exists():
            raise FileNotFoundError(f"Couldn't find file {file_path}")
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        


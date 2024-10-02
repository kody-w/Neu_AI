from langchain.tools import StructuredTool

class BasicSkill:
    def __init__(self, name, metadata):
        self.name = name
        self.metadata = metadata
        self.tool = StructuredTool.from_function(
            func=self.perform,
            name=self.name,
            description=self.metadata.get('description', '')
        )

    def perform(self, **kwargs):
        """
        Perform the skill's action. This method should be implemented by subclasses.
        
        Args:
            **kwargs: Arbitrary keyword arguments specific to the skill's implementation.
        
        Returns:
            The result of performing the skill's action.
        
        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("This method should be implemented by subclasses")
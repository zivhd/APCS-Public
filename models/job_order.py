class JobOrder:
    def __init__(
        self,
        start_date,
        completion_date,
        person_responsible,
        status,
        edit_reason,
        edit_person_responsible,
        edit_start_date,
        edit_completion_date,

        
        
    ):
        self.start_date = start_date
        self.completion_date = completion_date
        self.person_responsible = person_responsible
        self.status = status
        self.edit_reason = edit_reason
        self.edit_person_responsible =  edit_person_responsible 
        self.edit_start_date = edit_start_date
        self.edit_completion_date = edit_completion_date

        
    def to_dict(self):
        return {
            "start_date": self.start_date,
            "completion_date": self.completion_date,
            "person_responsible": self.person_responsible,
            "status": self.status,
            "edit_reason": self.edit_reason,
            "edit_person_responsible": self.edit_person_responsible,
            "edit_start_date" : self.edit_start_date,
            "edit_completion_date": self.edit_completion_date,
       
        }

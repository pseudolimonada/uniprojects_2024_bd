from src.utils import USER_DETAILS, USER_TYPE_DETAILS, APPOINTMENT_DETAILS, HOSPITALIZATION_DETAILS, SURGERY_DETAILS, PRESCRIPTION_DETAILS, PRESCRIPTION_MED_DETAILS, PAYMENT_DETAILS

def user_type(user_type: str):
    for user in USER_TYPE_DETAILS.keys():
        if user == user_type:
            return
    raise ValueError(f"User type {user_type} not found")

def user_register_details(user_type, payload: dict):
    missing_args = []

    for user_detail in USER_DETAILS:
        if user_detail not in payload:
            missing_args.append(user_detail)

    for user_detail in USER_TYPE_DETAILS[user_type]:
        if user_detail not in payload:
            missing_args.append(user_detail)
    
    if len(missing_args) != 0:
        raise ValueError(f"Missing arguments: {', '.join(missing_args)}")

def user_login_details(payload: dict):
    if 'username' not in payload or 'password' not in payload:
        raise ValueError("Missing username or password")        

def appointment_details(payload: dict):
    nurses = payload['nurses']

    if type(nurses) != list or len(nurses) == 0:
        raise ValueError("Nurses must be a list with at least one nurse")
    
    for nurse in nurses:
        if type(nurse) != list or len(nurse) != 2:
            raise ValueError("Nurse must be a list with id and role")

    missing_args = []

    for appointment_detail in APPOINTMENT_DETAILS:
        if appointment_detail not in payload:
            missing_args.append(appointment_detail)

    if len(missing_args) != 0:
        raise ValueError(f"Missing arguments: {', '.join(missing_args)}")

def surgery_details(payload: dict, hospitalization_id):
    nurses = payload['nurses']

    if type(nurses) != list or len(nurses) == 0:
        raise ValueError("Nurses must be a list with at least one nurse")
    
    for nurse in nurses:
        if type(nurse) != list or len(nurse) != 2:
            raise ValueError("Nurse must be a list with id and role")
        
    missing_args = []

    for surgery_detail in SURGERY_DETAILS:
        if surgery_detail not in payload:
            missing_args.append(surgery_detail)

    if hospitalization_id is None:
        for hospitalization_detail in HOSPITALIZATION_DETAILS:
            if hospitalization_detail not in payload:
                missing_args.append(hospitalization_detail)

    if len(missing_args) != 0:
        raise ValueError(f"Missing arguments: {', '.join(missing_args)}")

def prescription_details(payload: dict):
    type = payload['type']
    medicines = payload['medicines']
    missing_args = []

    if type != 'hospitalization' and type != 'appointment': #prevents sql injection as this will be a table name
        raise ValueError("Invalid prescription type")

    for medicine in medicines:
        for prescription_med_detail in PRESCRIPTION_MED_DETAILS:
            if prescription_med_detail not in medicine:
                raise ValueError(f"Missing {prescription_med_detail} in medicine")

    for prescription_detail in PRESCRIPTION_DETAILS:
        if prescription_detail not in payload:
            missing_args.append(prescription_detail)
    
    if len(missing_args) != 0:
        raise ValueError(f"Missing arguments: {', '.join(missing_args)}")

def payment_details(payload: dict):
    missing_args = []

    for payment_detail in PAYMENT_DETAILS:
        if payment_detail not in payload:
            missing_args.append(payment_detail)

    if len(missing_args) != 0:
        raise ValueError(f"Missing arguments: {', '.join(missing_args)}")
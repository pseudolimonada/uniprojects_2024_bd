# BD Project
All the documentation and source code for BD 2024 project LifeLink
Report link: https://www.overleaf.com/project/65f8cce4799e65445ec51df1

Follow the next steps to setup the DB.

# Create and setup DB
How: open PSQL and run these commands

```
psql -h localhost -U postgres
DROP DATABASE dbproj WITH(FORCE);
CREATE DATABASE dbproj;
CREATE USER dbproj PASSWORD "1234";
```

Run the schema script from onda in PGadmin, then execute these commands

```
psql -h localhost -U postgres -d dbproj;
GRANT ALL ON SCHEMA public to dbproj;
GRANT ALL ON ALL TABLES IN SCHEMA public TO dbproj;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO dbproj;
```

# Create indexes in DB
How: open PGAdmin and run this script in the query tool

```
CREATE INDEX idx_medication_id ON medication(id);
CREATE INDEX idx_medication_name ON medication(name);

CREATE INDEX idx_nurse_employee_person_id ON nurse(employee_person_id);
CREATE INDEX idx_doctor_employee_person_id ON doctor(employee_person_id);
CREATE INDEX idx_assistant_employee_person_id ON assistant(employee_person_id);
```

# Populate tables in DB
How: open PGAdmin and run this script in the query tool

```
INSERT INTO specialization (name)
VALUES
    ('Internal Medicine'),
    ('Surgery'),
    ('Pediatrics'),
    ('Dermatology'),
    ('Obstetrics and Gynecology'),
    ('Cardiology'),
    ('Gastroenterology'),
    ('Pulmonology'),
    ('Orthopedic Surgery'),
    ('Neurosurgery'),
    ('Spinal Neurosurgery');
	
INSERT INTO specialization_specialization (specialization_id, specialization_id1)
VALUES
    (6, 1), -- Cardiology > Internal Medicine
    (7, 1), -- Gastroenterology > Internal Medicine
    (8, 1), -- Pulmonology > Internal Medicine
    (10, 2), -- Neurosurgery > Surgery
	(11,10); -- Spinal Neurosurgery > Neurosurgery


INSERT INTO side_effect (name)
VALUES
    ('Nausea'),
    ('Headache'),
    ('Dizziness'),
    ('Dry mouth'),
    ('Sleepiness'),
    ('Constipation');

INSERT INTO medication (name)
VALUES
    ('Aspirin'),
    ('Ibuprofen'),
    ('Acetaminophen'),
    ('Amoxicillin'),
    ('Metformin'),
    ('Lisinopril');

INSERT INTO severity (level, medication_id, side_effect_id)
VALUES
    (2, 1, 1),  -- Aspirin causing Nausea with severity level 2
    (3, 1, 2),  -- Aspirin causing Headache with severity level 3
    (1, 2, 1),  -- Ibuprofen causing Nausea with severity level 1
    (4, 2, 3),  -- Ibuprofen causing Dizziness with severity level 4
    (2, 3, 4),  -- Acetaminophen causing Dry mouth with severity level 2
    (3, 4, 5),  -- Amoxicillin causing Sleepiness with severity level 3
    (1, 5, 6),  -- Metformin causing Constipation with severity level 1
    (2, 6, 1),  -- Lisinopril causing Nausea with severity level 2
    (3, 6, 2);  -- Lisinopril causing Headache with severity level 3
```


# Add triggers to DB
How: open PGAdmin and run this script in the query tool

```
-- Trigger for appointments
CREATE OR REPLACE FUNCTION _create_bill_from_appointment()
RETURNS trigger AS $$
BEGIN
    DECLARE
        bill_amount NUMERIC := 50.00;
    BEGIN
        INSERT INTO bill (amount, status, event_id)
        VALUES (bill_amount, 'open', NEW.event_id);
		RETURN NEW;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE EXCEPTION 'Error creating bill: %', SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER _create_bill_from_appointment_trigger
AFTER INSERT ON appointment
FOR EACH ROW
EXECUTE FUNCTION _create_bill_from_appointment();

-- Trigger for hospitalizations
CREATE OR REPLACE FUNCTION _create_bill_from_hospitalization()
RETURNS trigger AS $$
BEGIN
    DECLARE
        bill_amount NUMERIC := 0.00;
    BEGIN
        INSERT INTO bill (amount, status, event_id)
        VALUES (bill_amount, 'open', NEW.event_id);
		RETURN NEW;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE EXCEPTION 'Error creating bill: %', SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER _create_bill_from_hospitalization_trigger
AFTER INSERT ON hospitalization
FOR EACH ROW
EXECUTE FUNCTION _create_bill_from_hospitalization();

-- Trigger for surgery
CREATE OR REPLACE FUNCTION _update_bill()
RETURNS trigger AS $$
BEGIN
    UPDATE bill SET amount = amount + 200.00 WHERE event_id = NEW.hospitalization_event_id;
    RETURN NEW;
	IF NOT FOUND THEN
        RAISE EXCEPTION 'No bill updated';
    END IF;
END;

$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER _update_bill_trigger
AFTER INSERT ON surgery
FOR EACH ROW
EXECUTE FUNCTION _update_bill();
```
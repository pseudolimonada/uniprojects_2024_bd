# BD Project
All the documentation and source code for BD 2024 project LifeLink


Report link: https://www.overleaf.com/project/65f8cce4799e65445ec51df1



# EDGECASES
- Se um employee fosse um patient, o sistema não está preparado (ou será que está?) e teria de criar uma nova person entity com repetição de dados unicos (cartao cidadao, etc). 



# QUESTOES:
> permissões nao são representadas no diagrama, nem têm qualquer variavel (será que o authenticator consegue destingir sem variavel do tipo "person_type"?)
> é suposto fazermos sempre primary key artificial ou por exemplo side effects é nome+severidade?
> na modulação dos medicamentos assumimos um medicamento_type e medicamento_prescribed para não estar sempre a repetir o nome do medicamento ou?
> nas transações, é suposto fazer uma por cada feature a implementar certo? ou dividimos pelos principios de atomizar?
> para a app, é suposto usar python e http normal ou podemos usar coisas tipo o flask para simplificar o routing?




# PERMISSOES A IMPLEMENTAR
- só o assistant gere tudo o que é appointment surgery e hospitalization



# Instalar/Reinstalar a DB

```
DROP DATABASE dbproj WITH(FORCE);
CREATE DATABASE dbproj;
CREATE USER dbproj PASSWORD "1234";
(run schema script from onda)

psql -h localhost -U postgres -d dbproj;
GRANT ALL ON SCHEMA public to dbproj;
GRANT ALL ON ALL TABLES IN SCHEMA public TO dbproj;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO dbproj;
```


# Inserir especializações na DB

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

# TRIGGERS

# Adicionar um trigger à DB
1. abrir o PgAdmin
2. clicar em event (tabelas do lado esquerdo)
3. no canto superior esquerdo clicar no í cone que diz "all rows" quando metes o rato por cima
4. Ctrl+C, Ctrl+V pra dentro do terminal
5. executar

# Criação de bill por cada novo evento
```
CREATE SEQUENCE bill_id_sequence
START WITH 1
INCREMENT BY 1
NO CYCLE;

CREATE OR REPLACE FUNCTION _create_bill()
RETURNS trigger AS $$
BEGIN
    DECLARE
        bill_amount NUMERIC := 50.00;
    BEGIN
        INSERT INTO bills (amount, status, event_id)
        VALUES (bill_amount, False, new.event_id);

        COMMIT;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Error creating bill: %', SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER create_bill_trigger
AFTER INSERT ON event
FOR EACH STATEMENT
EXECUTE FUNCTION _create_bill();
```
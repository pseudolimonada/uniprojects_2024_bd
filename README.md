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
DROP DATABASE dbproj;
CREATE USER dbproj PASSWORD "1234";
CREATE DATABASE dbproj;
(run schema script from onda)

psql -h localhost -U postgres -d dbproj;
GRANT ALL ON SCHEMA public to dbproj;
GRANT ALL ON ALL TABLES IN SCHEMA public TO dbproj;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO dbproj;
```


# Inserir especializações na DB

```
INSERT INTO specialization (id, name)
VALUES
    (1, 'Internal Medicine'),
    (2, 'Surgery'),
    (3, 'Pediatrics'),
    (4, 'Dermatology'),
    (5, 'Obstetrics and Gynecology'),
    (6, 'Cardiology'),
    (7, 'Gastroenterology'),
    (8, 'Pulmonology'),
    (9, 'Orthopedic Surgery'),
    (10, 'Neurosurgery'),
	(11, 'Spinal Neurosurgery');
	
INSERT INTO specialization_specialization (specialization_id, specialization_id1)
VALUES
    (6, 1), -- Cardiology > Internal Medicine
    (7, 1), -- Gastroenterology > Internal Medicine
    (8, 1), -- Pulmonology > Internal Medicine
    (10, 2), -- Neurosurgery > Surgery
	(11,10); -- Spinal Neurosurgery > Neurosurgery
```
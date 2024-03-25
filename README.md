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



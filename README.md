# fastapi-autenticador

Um modelo de como aplicar a autenticação sem a necessidade senha utilizando o Fastapi como webservice, gerando um código, que é enviado por e-mail e depois retornando um token de autenticação válido.

<h5>Como instalar:</h5>

pip install -r requirements.txt

<h5>Recomendações:</h5>

É recomendado utilizar o ambiente serverless da AWS, instalando o webservice no Lambda para execução, o Api Gateway como "Porta de entrada" e o DynamoDB como banco de dados, e o Simple Email Service (SES) para disparar os e-mails.

Com isso, dependendo do volume de acessos, você continuará no free tier e não será cobrado para disponibilizar a solução.

Segue um tutorial utilizado como fonte para subir o serviço na Amazon:

https://towardsdatascience.com/fastapi-aws-robust-api-part-1-f67ae47390f9

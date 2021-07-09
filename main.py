from datetime import datetime, timedelta, date
from typing import Optional, List
from fastapi import Depends, FastAPI, HTTPException, status, Form, Body
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
import boto3
from boto3.dynamodb.conditions import Key, Attr
import uuid
import json
from mangum import Mangum


#### Random
SECRET_KEY = ""
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 720


dynamodb = boto3.resource('dynamodb', aws_access_key_id='',
                          aws_secret_access_key='',
                          region_name='')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_token_header(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"Authorization": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload['email'] is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

app = FastAPI()

origins = [
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def enviar_email(**kwargs):
    codigo = str(uuid.uuid4())[:8]
    texto = f"""
            <p><strong><span style="color: rgb(0, 0, 0);">Segue abaixo o c&oacute;digo de acesso solicitado:</span></strong></p>
            <p><br></p>
            <table style="font-family:'Lato',sans-serif;" role="presentation" cellpadding="0" cellspacing="0" width="100%" border="0">
                <tbody>
                    <tr>
                    <td style="overflow-wrap:break-word;word-break:break-word;padding:0px 40px;font-family:'Lato',sans-serif;" align="left">

                <div align="center">
                <!--[if mso]><table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-spacing: 0; border-collapse: collapse; mso-table-lspace:0pt; mso-table-rspace:0pt;font-family:'Lato',sans-serif;"><tr><td style="font-family:'Lato',sans-serif;" align="center"><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="" style="height:51px; v-text-anchor:middle; width:205px;" arcsize="27.5%" stroke="f" fillcolor="#18163a"><w:anchorlock/><center style="color:#FFFFFF;font-family:'Lato',sans-serif;"><![endif]-->
                    <a href="" target="_blank" style="box-sizing: border-box;display: inline-block;font-family:'Lato',sans-serif;text-decoration: none;-webkit-text-size-adjust: none;text-align: center;color: #FFFFFF; background-color: #18163a; border-radius: 14px; -webkit-border-radius: 14px; -moz-border-radius: 14px; width:auto; max-width:100%; overflow-wrap: break-word; word-break: break-word; word-wrap:break-word; mso-border-alt: none;border-top-width: 0px; border-top-style: dotted; border-top-color: #CCC; border-left-width: 0px; border-left-style: dotted; border-left-color: #CCC; border-right-width: 0px; border-right-style: dotted; border-right-color: #CCC; border-bottom-width: 0px; border-bottom-style: dotted; border-bottom-color: #CCC;">
                    <span style="display:block;padding:15px 40px;line-height:120%;"><span style="font-size: 18px; line-height: 21.6px;">{kwargs.get('codigo')}</span></span>
                    </a>
                <!--[if mso]></center></v:roundrect></td></tr></table><![endif]-->
                </div>

                    </td>
                    </tr>
                </tbody>
                </table>
            """

    tabela = dynamodb.Table('')
    tabela.put_item(
        Item={
            "assunto": "Código de Acesso",
            "chamada": "Código de Acesso",
            "destinatarios": [kwargs.get('email')],
            "id": codigo,
            "texto": texto
        }
    )

    return True


class Token(BaseModel):
    access_token: str
    token_type: str


class Access:

    def __init__(self, **kwargs):
        self

    def checar(self, **kwargs):
        table = dynamodb.Table('')

        response = table.scan(
            FilterExpression=Attr('codigo').eq(kwargs.get('codigo'))
        )
        if response['Items']:
            return response['Items'][0]
        else:
            return False

    def enviar(self, **kwargs):
        codigo = str(uuid.uuid4())[:8]

        table = dynamodb.Table('')
        response = table.query(
            KeyConditionExpression=Key('email').eq(kwargs.get('email'))
        )
        if response['Items']:
            table.update_item(
                Key={
                    'email': kwargs.get('email')
                },
                UpdateExpression='SET codigo = :val1',
                ExpressionAttributeValues={
                    ':val1': codigo
                }
            )
            enviar_email(email=kwargs.get('email'), codigo=codigo)
            return True
        else:
            return False


@ app.get("/")
def read_root():
    return {"Hello": "World"}


@ app.post("/gerar/{email}", status_code=201)
def gerar_codigo(email: str):
    acesso = Access()
    usuario = acesso.enviar(email=email)
    if usuario:
        return "Updated"
    else:
        raise HTTPException(status_code=400, detail="Usuário não encontrado")


@ app.post("/verificar/{codigo}", status_code=200)
def verificar_codigo(codigo: str):
    acesso = Access()
    c = acesso.checar(codigo=codigo)
    return {"codigo": c}


@ app.post("/token/{codigo}", response_model=Token)
async def login_for_access_token(codigo: str):
    acesso = Access()
    user = acesso.checar(codigo=codigo)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de acesso inválida",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"email": user['email'], "nome": user['nome']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


## EM DESENVOLVIMENTO
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='127.0.0.1', port=5000, reload=True, workers=2)


## EM PRODUCAO NO LAMBDA AWS
# handler = Mangum(app)

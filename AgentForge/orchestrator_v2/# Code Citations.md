# Code Citations

## License: unknown
https://github.com/TONGOLDDIAMOND/server-bd/blob/d802c330f9a2f324c77b3516c5dbb6651531b694/fastapi_server.py

```
(product_id: int, db: Session = Depends
```


## License: unknown
https://github.com/TONGOLDDIAMOND/server-bd/blob/d802c330f9a2f324c77b3516c5dbb6651531b694/fastapi_server.py

```
(product_id: int, db: Session = Depends(get_db)):
    product
```


## License: unknown
https://github.com/TONGOLDDIAMOND/server-bd/blob/d802c330f9a2f324c77b3516c5dbb6651531b694/fastapi_server.py

```
(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_i
```


## License: unknown
https://github.com/TONGOLDDIAMOND/server-bd/blob/d802c330f9a2f324c77b3516c5dbb6651531b694/fastapi_server.py

```
(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(
```


## License: unknown
https://github.com/TONGOLDDIAMOND/server-bd/blob/d802c330f9a2f324c77b3516c5dbb6651531b694/fastapi_server.py

```
(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found
```


## License: MIT
https://github.com/opensourceducation/Digital-Accordions/blob/6fb61ab95908fc03c326ac09a555547f39a52e35/api/services/login/dockerfile

```
slim
```


## License: unknown
https://github.com/angelika233/FastAPI_PostgreSQL/blob/9318b2325d6a9309c278a1471a12238facff4e93/Dockerfile.fastapi

```
slim
```


## License: MIT
https://github.com/opensourceducation/Digital-Accordions/blob/6fb61ab95908fc03c326ac09a555547f39a52e35/api/services/login/dockerfile

```
slim

WORKDIR /app

COPY requirements
```


## License: unknown
https://github.com/angelika233/FastAPI_PostgreSQL/blob/9318b2325d6a9309c278a1471a12238facff4e93/Dockerfile.fastapi

```
slim

WORKDIR /app

COPY requirements
```


## License: MIT
https://github.com/opensourceducation/Digital-Accordions/blob/6fb61ab95908fc03c326ac09a555547f39a52e35/api/services/login/dockerfile

```
slim

WORKDIR /app

COPY requirements.txt .
R
```


## License: unknown
https://github.com/angelika233/FastAPI_PostgreSQL/blob/9318b2325d6a9309c278a1471a12238facff4e93/Dockerfile.fastapi

```
slim

WORKDIR /app

COPY requirements.txt .
R
```


## License: MIT
https://github.com/opensourceducation/Digital-Accordions/blob/6fb61ab95908fc03c326ac09a555547f39a52e35/api/services/login/dockerfile

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-
```


## License: unknown
https://github.com/angelika233/FastAPI_PostgreSQL/blob/9318b2325d6a9309c278a1471a12238facff4e93/Dockerfile.fastapi

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-
```


## License: MIT
https://github.com/opensourceducation/Digital-Accordions/blob/6fb61ab95908fc03c326ac09a555547f39a52e35/api/services/login/dockerfile

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```


## License: unknown
https://github.com/angelika233/FastAPI_PostgreSQL/blob/9318b2325d6a9309c278a1471a12238facff4e93/Dockerfile.fastapi

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```


## License: MIT
https://github.com/opensourceducation/Digital-Accordions/blob/6fb61ab95908fc03c326ac09a555547f39a52e35/api/services/login/dockerfile

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8
```


## License: unknown
https://github.com/angelika233/FastAPI_PostgreSQL/blob/9318b2325d6a9309c278a1471a12238facff4e93/Dockerfile.fastapi

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8
```


## License: MIT
https://github.com/opensourceducation/Digital-Accordions/blob/6fb61ab95908fc03c326ac09a555547f39a52e35/api/services/login/dockerfile

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main
```


## License: unknown
https://github.com/angelika233/FastAPI_PostgreSQL/blob/9318b2325d6a9309c278a1471a12238facff4e93/Dockerfile.fastapi

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main
```


## License: MIT
https://github.com/opensourceducation/Digital-Accordions/blob/6fb61ab95908fc03c326ac09a555547f39a52e35/api/services/login/dockerfile

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0
```


## License: unknown
https://github.com/angelika233/FastAPI_PostgreSQL/blob/9318b2325d6a9309c278a1471a12238facff4e93/Dockerfile.fastapi

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0
```


## License: MIT
https://github.com/opensourceducation/Digital-Accordions/blob/6fb61ab95908fc03c326ac09a555547f39a52e35/api/services/login/dockerfile

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "
```


## License: unknown
https://github.com/angelika233/FastAPI_PostgreSQL/blob/9318b2325d6a9309c278a1471a12238facff4e93/Dockerfile.fastapi

```
slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "
```


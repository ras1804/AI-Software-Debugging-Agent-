from fastapi import FastAPI
app=FastAPI()

@app.get("/orders")
def orders(quantity:int=1):
    total=100/quantity
    return {"total":total}

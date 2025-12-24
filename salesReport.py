
def sales(fileName):
    with open(fileName,'r') as f :
        line=f.readlines()
    invoice=0
    maxprice=0
    for i in line[1:]:
        c=i.strip().split(",")
        value=float(c[4][2:])
    
        inv=int(c[5])
        if value>maxprice :
            maxprice=value
            invoice=inv
    print("Highest maxprice and invoice Value : " , maxprice , invoice)
    
def highestInvoice(fileName) :
    with open(fileName,'r') as f :
        line=f.readlines()
    d={}
    for i in line[1:]:
        c=i.strip().split(",")
        value=float(c[4][2:])
        d[c[1]] = d.get(c[1],0)+value
    maxPrice = 0.0
    date=""
    for i in d :
        if maxPrice<d[i]:
            maxPrice =d[i]
            date =i      
    print("highest invoice value date " ,date ,"Max price : ",maxPrice)
 
def highestCustomer(fileName) :
    with open(fileName,'r') as f :
        line=f.readlines()
    d={}
    for i in line[1:]:
        c=i.strip().split(",")
        value=float(c[4][2:])
        d[c[6]] = d.get(c[6],0)+value
    maxPrice = 0.0
    customerId=""
    for i in d :
        if maxPrice<d[i]:
            maxPrice =d[i]
            customerId =i      
    print("highest invoice value customerId: ",customerId ,"Max price : ",maxPrice)
        
sales("sales.csv")
highestInvoice("sales.csv")
highestCustomer("sales.csv")
        

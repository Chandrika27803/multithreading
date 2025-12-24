#Logic
# Take the CSV file
# clean the data
# load and check if all values are there
# Calculate per day revenue
# calculate revenue for city
# calculate total revenue for each item
# iterate through each line and check whether all 9 column values are there or not
# detect suspicious records
# check for misssing date, city, negative or zero amounts and duplicate invoice numbers
# export the clean data to file.

# Algo:-

# for total revenue per day create a empty dic
# get the date and amount from sales data
# add the amount to dates total
# print all the dates with there amounts after processing.
# Show total revenue per city, create a dic for city and repeat the same process.
# get city name and amount
# after all records are read print total revenue per city

# Algo for top n items by revenue-
# Defining invoice as primary key or unique column
# considering five column category, invoice, quantity, cities and price.
# sorting the category column
# going for 'for' loop, for certain category for increasing the count of purchase and adding the price
# checking for the revenue generated in certain cities.
# total cities revenue
# Print output.
# We are getting city name from previous code (real data)

import os
cities = []
error = []

def revDay(fileName, path):
    d={}
    with open(fileName,'r') as f:
        lines=f.readlines()
    ensure_file(path)
    for line in lines[1:]:
       
        c=line.strip().split(",")
        
        
        
        if len(c)==10:
            with open(path,'a') as file:
                file.write(line)
                file.write("\n")
            date=c[1]
            price=float(c[4][2:])
            if date in d:
                d[date]+=price
            else:
                d[date]=price
        else:
            error.append(c)
  #  print(error)
   
def revCity(fileName):
    a={}
    with open(fileName, 'r') as f:
        lines = f.readlines()
    for line in lines[1:]:
       
        c=line.strip().split(",")
        if len(c)==10:
           
            city=c[7]
            price=float(c[4][2:])
            if city in a:
                a[city]+=price
            else:
                a[city]=price
#        else:
#            error.append(c)
    print(a)
    for k,v in a.items():
        cities.append(k)
    #cities = a.keys()
    print(cities)
   
def category(fileName):
    b1={}
    b2={}
    b3={}
    b4={}
    b5={}
    with open(fileName, 'r') as f:
        lines = f.readlines()
    for line in lines[1:]:
        c=line.strip().split(",")
        if len(c)==10:
           
            city=c[7]
            price=float(c[4][2:])
            quantity = int(c[2])
            cat = c[8]
            if city == cities[0]:
                if cat in b1:
                    b1[cat][0] += quantity
                    b1[cat][1] += price
                else:
                    b1[cat] = [quantity, price]
                   
            elif city == cities[1]:
                if cat in b2:
                    b2[cat][0] += quantity
                    b2[cat][1] += price
                else:
                    b2[cat] = [quantity, price]
                   
            elif city == cities[2]:
                if cat in b3:
                    b3[cat][0] += quantity
                    b3[cat][1] += price
                else:
                    b3[cat] = [quantity, price]
                   
            elif city == cities[3]:
                if cat in b4:
                    b4[cat][0] += quantity
                    b4[cat][1] += price
                else:
                    b4[cat] = [quantity, price]
                   
            else:
                if cat in b5:
                    b5[cat][0] += quantity
                    b5[cat][1] += price
                else:
                    b5[cat] = [quantity, price]
                   
    print("Bangalore: ",b1)
    print("Kochi: ",b2)
    print("Pune: ",b3)
    print("Noida: ",b4)
    print("chennai: ",b5)
   
def get_value(item):
    return item[1]
   
def nitems(n,fileName):
    a={}
    with open(fileName, 'r') as f:
        lines = f.readlines()
    for line in lines[1:]:
       
        c=line.strip().split(",")
        if len(c)==10:
           
            item=c[3]
            price=float(c[4][2:])
            if item in a:
                a[item]+=price
            else:
                a[item]=price
#        else:
#            error.append(c)
   # print(a)
   
    b = sorted(a.items(),key = get_value, reverse = True)
    #print(dict(b))
    #d = dict(b)
   # while n>0:
    for i in range(n):
        print(b[i])

       
def ensure_file(path: str):
    if not os.path.exists(path):
        open(path, "w").close()
revDay("sales 1.csv", "Clean.csv")
revCity("sales 1.csv")
category("sales 1.csv")
n = int(input("Enter: "))

nitems(n,"sales 1.csv")

#Export clean Data file
#Read the file
#Check data is valid or not
#Length of the particular line
#Length equals to required length,
#Correct data will be stored in another file









	


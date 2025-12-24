monthly_max = {}
monthly_total = {}
monthly_count = {}
monthly_max_invoice = {}
monthly_avg = {}
def monthly_report(fileName):
    with open(fileName,"r") as f:
        lines = f.readlines()
        for line in lines[1:]:
            date = line.strip().split(",")[1]
            month = date.strip().split("-")[1]
            if month in monthly_count:
                monthly_count[month] += 1
            else:
                monthly_count[month] = 1

            price = float(line.strip().split(",")[4][2:])
            invoice_no = int(line.strip().split(",")[5])

            if month in monthly_total:
                monthly_total[month] += price
            else:
                monthly_total[month] = price

            if month in monthly_max:
                if monthly_max[month] < price:
                    monthly_max[month] = price
                    monthly_max_invoice[month] = invoice_no
            else:
                monthly_max[month] = price


    for k in monthly_total:
        if k not in monthly_avg:
            monthly_avg[k] = round((monthly_total[k] / monthly_count[k]),2)

    print("The maximum sale for each month are as follows:",monthly_max)
    print("The average sale per month in as follows:",monthly_avg)
    print("For each month the invoice with highest sales is as follows:",monthly_max_invoice)


monthly_report("sales.csv") with open("report.txt","w") as f:
    f.write("The maximum sale for each month are as follows:")
    f.write(f"{monthly_max}")
    f.write("\n")
    f.write("The average sale per month in as follows:")
    f.write(f"{monthly_avg}")
    f.write("\n")
    f.write("For each month the invoice with highest sales is as follows:")
    f.write(f"{monthly_max_invoice}")
    f.write("\n")



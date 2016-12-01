import json
import collections
import sys
import re
import bisect
import numpy

class product_match():
    def __init__(self):
        self.products = []
        self.listings = []
        self.model_by_manufacturer = collections.defaultdict(dict)
        self.matched_by_model = collections.defaultdict(list)

    #currency conversion for price check
    def convert_to_usd(self,currency, price):
        xrate2usd = {}
        #exchange rate as of Nov, 2016
        xrate2usd["gbp"] = 1.24
        xrate2usd["eur"] = 1.06
        xrate2usd["cad"] = 0.74
        xrate2usd["usd"] = 1

        currency = currency.lower()
        if currency in xrate2usd:
            return round(price*xrate2usd[currency], 2)
        else:
            #no such currency in table
            print "currency: {}".format(currency)
            return None
    #currency conversion for price check
    def convert_usd_to_currency(self, currency, price):
        xrate2usd = {}
        #exchange rate as of Nov, 2016
        xrate2usd["gbp"] = 1.24
        xrate2usd["eur"] = 1.06
        xrate2usd["cad"] = 0.74
        xrate2usd["usd"] = 1

        currency = currency.lower()
        if currency in xrate2usd:
            return round(price/xrate2usd[currency], 2)
        else:
            #no such currency in table
            print "currency: {}".format(currency)
            return None

    #read products from file
    def read_products(self, file_name="products.txt"):
        with open(file_name) as f:
            for line in f:
                data = json.loads(line)
                self.products.append(data)
    #read listings from file
    def read_listings(self, file_name="listings.txt"):
        with open(file_name) as f:
            for line in f:
                data = json.loads(line)
                self.listings.append(data)

    #create hashmap to speed up title search by manufacturer
    def sort_product_by_manufacturer(self):
        for product in self.products:
            key = product["manufacturer"].lower()
            model = product["model"].lower()
            product_name = product["product_name"].lower()
            self.model_by_manufacturer[key][model] = product_name

    #catch common patterns with numbers. don't search model in these patterns
    def ignore_patterns(self, title):
        ignore_pattern = []
        pattern1 = "[0-9.,]+[ ]*m(ega)?[ ]*p(ix)?(el)?[s]*[., \]]+" # 10.2 MegaPixels
        pattern2 = "[0-9]*\-[0-9]*mm" #70-300mm
        pattern3 = "[0-9]+[ ]*mm" #1000mm
        pattern4 = "[ ]+[0-9]+[.,]*[0-9]*[\- ][\"]*inch[., \]]+" #2.7 inch

        #did not include patterns in a list because their results parse differently
        pat1 = re.compile(pattern1, re.IGNORECASE)
        pat2 = re.compile(pattern2, re.IGNORECASE)
        pat3 = re.compile(pattern3, re.IGNORECASE)
        pat4 = re.compile(pattern4, re.IGNORECASE)
        match = pat1.search(title)
        if match:
            match = match.group(0)
            match = match.lstrip(",.").split("m")[0].strip()
            match = match.replace(",",".")
            ignore_pattern.append(match)

        match = pat2.search(title)
        if match:
            match = match.group(0)
            match = match.strip(",. ").split("m")[0].split("-")
            for item in match:
                ignore_pattern.append(match)

        match = pat3.search(title)
        if match:
            match = match.group(0)
            match = match.strip(",. ").split("m")[0].strip()
            ignore_pattern.append(match)

        match = pat4.search(title)
        if match:
            match = match.group(0)
            match = match.strip(",. ").split("inch")[0].strip(" -")
            ignore_pattern.append(match)

        if ignore_pattern:
            #print ignore_pattern
            pass

        return ignore_pattern

    #first step of matching. check if model name is in title.
    def match_by_model_name(self):
        for idx, listing in enumerate(self.listings):
            manufacturer = listing["manufacturer"].lower()
            #all lowercase
            title = listing["title"].lower()
            if manufacturer in self.model_by_manufacturer:
                models = self.model_by_manufacturer[manufacturer].keys()
                matched_models = []
                ignore_pattern = self.ignore_patterns(title)
                match_result = ""

                for model in models:
                    #search if model name is in title as one word
                    if " "+model+" " in title:
                        if title.count(model) > ignore_pattern.count(model):
                            matched_models.append(model)

                if len(matched_models) == 1:
                    #one and only match. Good.
                    match_result = matched_models[0]
                elif len(matched_models) == 0:
                    #no match at all
                    match_result = ""
                    pass
                else:
                    #more than one match. Need to check if overlapping pattern
                    #if overlap, use the longest pattern
                    matched_models.sort(key=len)
                    more_than_one_models = False
                    for idx, item in enumerate(matched_models[:-1]):
                        if not item in matched_models[idx+1]:
                            more_than_one_models = True
                    if more_than_one_models:
                        #no match
                        pass
                    else:
                        #use longest string as match
                        match_result = matched_models[-1]
                    
                if match_result != "":
                    product_name = self.model_by_manufacturer[manufacturer][match_result]
                    self.matched_by_model[product_name].append(listing)
            else:
                #no brand name
                pass

    def price_check(self):
        #sanity check on the prices. if price too low or too high, discard
        for product in self.matched_by_model:
            outliers = collections.defaultdict(list)
            global_prices = []
            price2listing = collections.defaultdict(lambda: collections.defaultdict(list))

            for listing in self.matched_by_model[product]:
                price = round(float(listing["price"]),2)
                currency = listing["currency"].lower()
                price_in_usd = self.convert_to_usd(currency, price)
                global_prices.append(price_in_usd)
                price2listing[currency][price].append(listing)
                
            #calculate global average, all converted to usd
            global_mean = round(numpy.mean(global_prices), 2)
            global_std = round(numpy.std(global_prices), 2)

            for currency in price2listing:
                mean = round(numpy.mean(price2listing[currency].keys()), 2)
                std = round(numpy.std(price2listing[currency].keys()), 2)

                curr_global_mean = self.convert_usd_to_currency(currency, global_mean)
                curr_global_std = self.convert_usd_to_currency(currency, global_std)

                for value in price2listing[currency].keys():
                    #assuming normal distribution. anything above or below 
                    #mean +- 3*std is outlier. discard these matches
                    
                    #also compare price to global mean, if price is above 3 times global mean
                    #or below 20% global mean, discard as outliers
                    if (value > (mean+3*std) or value < (mean-3*std) or
                        value > (curr_global_mean*3.0) or 
                        value < (curr_global_mean/5.0)):
                        
                        outliers[product].extend(price2listing[currency][value])

            #remove outlier listings from the original match table
            for outlier in outliers[product]:
                self.matched_by_model[product].remove(outlier)

    #write result to file: result.txt
    def write_result(self, filename = "result.txt"):
        with open(filename, 'w') as f:
            for prod in self.matched_by_model:
                temp = {}
                temp["product_name"] = prod
                temp["listings"] = self.matched_by_model[prod]
                data = json.dumps(temp)
                f.write(data+"\n")
            print "result written to file: {}".format(filename)

def main():
    obj = product_match()
    obj.read_products()
    obj.read_listings()

    obj.sort_product_by_manufacturer()
    obj.match_by_model_name() 
    obj.price_check()
    obj.write_result()

    print "total products: {}".format(len(obj.products))
    print "total listings: {}".format(len(obj.listings))
    print "products matched: {}/{}".format(len(obj.matched_by_model.keys()), len(obj.products))
    print "total listings matched: {}/{}".format(sum(len(x) for x in obj.matched_by_model.values()), len(obj.listings))
    


if __name__ == "__main__":
    main()    
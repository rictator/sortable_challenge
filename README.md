# sortable_challenge
sortable coding challenge. Match camera models to listings.

Challenge Data<br />
products.txt – Contains around 700 products<br />
listings.txt – Contains about 20,000 product listings

Output File:<br />result.txt

Challenge Script:<br />challenge.py

install numpy package for python (https://docs.scipy.org/doc/numpy-1.10.1/user/install.html). It is used for calculating mean and standard deviation.

Usage:<br />python challenge.py

The script will read products.txt and listings.txt in the same directory, and output the result to result.txt

Code logic:<br />
Find titles with model number in its name.<br />
Look for patterns to ignore in the title. Ex: "12" in "12 MegaPixels". "70" and "300" in "70-300mm"<br />
Avoid duplicate title matches<br />
Check if price is normal. (reasonable deviation from market average)<br />
write result<br />












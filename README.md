# DEFT
# Installation
1.	Open a command prompt and navigate to the directory where you want to install the DEFT
2.	Clone the repository `git clone https://gitlab.epri.com/pmev001/deft.git`
    a.	Note, this URL will be replaced by the github url for end users
3.	Ensure python 3 and virtualenv are installed `pip install virtualenv`
4.	Change directory into the deft directory 
5.	Create a virtual environment ` virtualenv deftvenv -p C:\path\to\your\python\install\python.exe `
6.	Activate the virtual environment ` .\deftvenv\Scripts\activate`
7.	Install all requirements `pip install -r requirements.txt`
8.	Run the DEFT `python DEFT.py`


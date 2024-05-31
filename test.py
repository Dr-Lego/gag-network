from selenium import webdriver

def my_python_function():
    # Your Python code here
    print("Python function called!")
    
    
# Create a new instance of the webdriver
driver = webdriver.Chrome()

# Navigate to the web page
driver.get("https://example.com")

# Add an event listener in JavaScript that calls the Python function
driver.execute_script("""
    document.addEventListener('click', function() {
        window.pyFunction();
    });

    window.pyFunction = function() {
        return window.pySelenium.my_python_function();
    };
""")

# Call the Python function from the JavaScript code
driver.execute_script("window.pyFunction()")
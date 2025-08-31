import streamlit as st

def main():
    st.write("Testing Streamlit Setup")
    st.write("If you can see this, Streamlit is working correctly!")
    
    st.sidebar.write("Sidebar Test")
    if st.sidebar.button("Click Me"):
        st.write("Button clicked!")

if __name__ == "__main__":
    main()

from bs4 import BeautifulSoup
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["crawler_db"]
professors_collection = db["professors"]

def parse_faculty_data(html):
    soup = BeautifulSoup(html, "html.parser")
    professors = []

    #find all faculty member containers
    faculty_divs = soup.find_all("div", class_="clearfix")

    for faculty in faculty_divs:
        #Name
        name = faculty.find("h2").text.strip() if faculty.find("h2") else None
        if not name:
            continue
        print(f"Extracting data for: {name}")

        # Initialize fields
        title, office, phone, email, website = None, None, None, None, None

        details = faculty.find("p")
        if details:
            for strong in details.find_all("strong"):
                label = strong.text.strip().rstrip(':')
                next_node = strong.next_sibling

                def clean_text(content):
                    if isinstance(content, str):
                        return content.strip()
                    elif content and content.name == "a":
                        return content.text.strip()
                    return None

                if label == "Title":
                    title = clean_text(next_node)
                elif label == "Office":
                    office = clean_text(next_node)
                elif label == "Phone":
                    phone = clean_text(next_node)
                elif label == "Email":
                    email_tag = strong.find_next("a", href=lambda href: href and href.startswith("mailto:"))
                    email = email_tag.text.strip() if email_tag else None
                elif label == "Web":
                    web_tag = strong.find_next("a", href=True)
                    website = web_tag["href"].strip() if web_tag else None

        #Debug
        print(f"Extracted -> Title: {title}, Office: {office}, Phone: {phone}, Email: {email}, Website: {website}")

        #append professors
        professors.append({
            "name": name,
            "title": title if title else "N/A",
            "office": office if office else "N/A",
            "phone": phone if phone else "N/A",
            "email": email if email else "N/A",
            "website": website if website else "N/A"
        })

    return professors

def main():
    target_page = db["pages"].find_one({"url": "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"})
    if not target_page:
        print("Faculty page not found in the database.")
        return

    html = target_page.get("html", "")
    if not html:
        print("HTML content is empty.")
        return

    #main function
    professors = parse_faculty_data(html)

    #log and store the parsed data in the database
    for professor in professors:
        if not professor["name"]:
            print("Skipping incomplete professor entry.")
            continue
        print(f"Inserting into DB: {professor}")
        professors_collection.insert_one(professor)
        print(f"Inserted: {professor['name']}")

if __name__ == "__main__":
    main()

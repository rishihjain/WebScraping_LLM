# Testing Examples for Multi-Website Comparison

## 🛒 E-Commerce Examples

### Example 1: Product Comparison
**Domain:** E-Commerce

**URLs:**
```
https://www.amazon.com/dp/B08N5WRWNW
https://www.bestbuy.com/site/apple-airpods-pro-2nd-generation-white/6527850.p
```

**Instruction:**
```
Extract product name, price, rating, number of reviews, key features, and availability status
```

---

### Example 2: E-Commerce Homepage Comparison
**Domain:** E-Commerce

**URLs:**
```
https://www.amazon.com
https://www.ebay.com
```

**Instruction:**
```
Extract main navigation categories, featured products or deals, search functionality description, and key site features
```

---

## 📰 News Examples

### Example 1: News Article Comparison
**Domain:** News & Media

**URLs:**
```
https://www.bbc.com/news/technology
https://www.theverge.com
```

**Instruction:**
```
Extract main headlines, article categories, featured stories, and publication dates
```

---

### Example 2: Tech News Comparison
**Domain:** News & Media

**URLs:**
```
https://techcrunch.com
https://www.wired.com
```

**Instruction:**
```
Extract top headlines, article titles, categories, and featured content
```

---

## 💼 Business Examples

### Example 1: Company Pages
**Domain:** Business & Finance

**URLs:**
```
https://www.apple.com
https://www.microsoft.com
```

**Instruction:**
```
Extract company description, main products/services, key features, and value propositions
```

---

## 💼 Job Listings Examples

### Example 1: Job Board Comparison
**Domain:** Job Listings

**URLs:**
```
https://www.indeed.com/jobs?q=software+engineer&l=San+Francisco%2C+CA
https://www.linkedin.com/jobs/search/?keywords=software%20engineer&location=San%20Francisco
```

**Instruction:**
```
Extract job titles, company names, locations, salary ranges (if available), and job types
```

---

## 🏠 Real Estate Examples

### Example 1: Property Listings
**Domain:** Real Estate

**URLs:**
```
https://www.zillow.com/homes/for_sale/
https://www.realtor.com
```

**Instruction:**
```
Extract property types, price ranges, locations, and key features available on the homepage
```

---

## 🍽️ Restaurant Examples

### Example 1: Restaurant Listings
**Domain:** Restaurant & Food

**URLs:**
```
https://www.yelp.com/search?find_desc=restaurants&find_loc=San+Francisco%2C+CA
https://www.tripadvisor.com/Restaurants-g60713-San_Francisco_California.html
```

**Instruction:**
```
Extract restaurant names, cuisines, ratings, price ranges, and locations
```

---

## 🌐 General Examples (Easy to Test)

### Example 1: Simple Website Comparison
**Domain:** General

**URLs:**
```
https://example.com
https://www.wikipedia.org
```

**Instruction:**
```
Extract main headings, key content sections, navigation structure, and main purpose of the website
```

---

## 🎯 Recommended Test (Easiest to Start)

**Domain:** News & Media

**URLs:**
```
https://www.bbc.com/news
https://www.cnn.com
```

**Instruction:**
```
Extract main headlines, article titles, categories, and featured stories
```

**Why this is good for testing:**
- Both sites are publicly accessible
- They have similar content structure
- Easy to compare (both are news sites)
- Likely to work without blocking
- Clear differences to highlight in comparison

---

## 📝 Testing Tips

1. **Start Simple:** Use the "General" domain first to test basic functionality
2. **Check URLs First:** Make sure the URLs are accessible in your browser
3. **Clear Instructions:** Be specific about what you want to extract
4. **Enable Comparison:** Don't forget to check the "Enable Multi-Website Comparison" checkbox
5. **Wait for Results:** Scraping can take 30-60 seconds per website

---

## ⚠️ Note

Some websites may block automated access. If you get timeout errors:
- Try different URLs
- Wait a few minutes and try again
- Use simpler, more accessible sites for initial testing


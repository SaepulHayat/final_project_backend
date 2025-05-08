# Book Filtering API Documentation

Provides a way to retrieve a list of books with various filtering, sorting, and pagination options.

- **Method:** `GET`
- **URL:** `/api/v1/books/`

## Query Parameters

All parameters are optional and should be sent as query string parameters.

| Parameter        | Type                     | Optional | Default      | Description                                                                                                 | Example                      |
| ---------------- | ------------------------ | -------- | ------------ | ----------------------------------------------------------------------------------------------------------- | ---------------------------- |
| `categories`     | String                   | Yes      | N/A          | Comma-separated category names. Filters for books belonging to ALL specified categories (case-insensitive). | `categories=Fiction,Mystery` |
| `publisher_name` | String                   | Yes      | N/A          | Filter by publisher name (case-insensitive, partial match).                                                 | `publisher_name=Penguin`     |
| `author_name`    | String                   | Yes      | N/A          | Filter by author's full name (case-insensitive, partial match).                                             | `author_name=John Doe`       |
| `seller_name`    | String                   | Yes      | N/A          | Filter by seller's (user's) full name (case-insensitive, partial match).                                    | `seller_name=Alice Smith`    |
| `city_name`      | String                   | Yes      | N/A          | Filter by the city name of the seller's location (case-insensitive, partial match).                         | `city_name=New York`         |
| `min_rating`     | Float                    | Yes      | N/A          | Filter by minimum average book rating.                                                                      | `min_rating=4.0`             |
| `min_price`      | Float                    | Yes      | N/A          | Filter by minimum book price.                                                                               | `min_price=10.99`            |
| `max_price`      | Float                    | Yes      | N/A          | Filter by maximum book price.                                                                               | `max_price=25.50`            |
| `search`         | String                   | Yes      | N/A          | Search term for book titles (case-insensitive, partial match).                                              | `search=Adventure`           |
| `page`           | Integer                  | Yes      | `1`          | Page number for pagination.                                                                                 | `page=2`                     |
| `per_page`       | Integer                  | Yes      | `12`         | Number of items per page for pagination.                                                                    | `per_page=10`                |
| `sort_by`        | String                   | Yes      | `created_at` | Field to sort by. Options: `price`, `title`, `rating`, `created_at`.                                        | `sort_by=price`              |
| `order`          | String (`asc` or `desc`) | Yes      | `desc`       | Sort order.                                                                                                 | `order=asc`                  |

## Example Request

`GET /api/v1/books/?categories=Science%20Fiction,Technology&publisher_name=Tech%20Press&min_price=15&sort_by=rating&order=desc`

## Success Response

**Status Code:** `200 OK`

**Body:**

```json
{
  "status": "success",
  "message": "Books retrieved successfully",
  "data": {
    "books": [
      {
        "id": 1,
        "title": "The Future of AI",
        "author": { "id": 1, "full_name": "Dr. Eva Core" },
        "publisher": { "id": 2, "name": "Tech Press Global" },
        "price": "22.50",
        "rating": "4.70",
        "user": {
          "id": 5,
          "full_name": "BookSeller123",
          "location": {
            "city": { "name": "Techville" },
            "state": { "name": "Innovate State" },
            "country": { "name": "Futura" }
          }
        },
        "categories": [
          { "id": 3, "name": "Technology" },
          { "id": 7, "name": "Science Fiction" }
        ]
        // ... other simple book fields
      }
      // ... more books
    ],
    "total": 25,
    "pages": 3,
    "current_page": 1
  },
  "error": null,
  "status_code": 200
}
```

_(Note: The exact fields returned for each book depend on the `to_simple_dict()` method in the `Book` model. This is a representative example.)_

## Error Responses

- If `min_rating`, `min_price`, or `max_price` are provided with values that cannot be converted to a float, the filter for that specific parameter might be ignored by the service, or a generic error could be returned depending on overall server-side error handling for query parameter type conversion.
- Standard HTTP error codes (e.g., 500 for server errors, 400 for bad requests if query parameter validation is stricter at the route level) may also be returned.

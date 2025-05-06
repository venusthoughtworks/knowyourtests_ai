test_patterns = {
    "unit": [
        # === General Patterns ===
        r"@Test",                           # Java/Kotlin
        r"test\(",                          # Python, Kotlin, JS
        r"def\s+test_",                     # Python
        r"describe\(.*\)", r"it\(.*\)",     # JS/TS/Mocha/Jest
        r"should(Be|Equal|Not)",            # Kotest, RSpec
        r"assert.*",                        # Universal

        # === Language Specific ===
        # Java/Kotlin
        r"import\s+org\.junit", r"mockk\(", r"Mockito",
        # Python
        r"import\s+unittest", r"pytest",
        # JS/TS
        r"jest", r"mocha", r"chai",
        # Ruby
        r"require\s+['\"]rspec", r"RSpec.describe",
        # Go
        r"func\s+Test[A-Z]", r"testing.T",
        # PHP
        r"use\s+PHPUnit", r"extends\s+TestCase",
        # C#
        r"[TestMethod]", r"using\s+Microsoft.VisualStudio.TestTools.UnitTesting",
        # Scala
        r"FlatSpec", r"FunSuite",
        # Dart
        r"test\(", r"expect\(",
        # Rust
        r"#\[test\]", r"assert_eq!",
    ],

    "integration": [
        # === General ===
        r"@SpringBootTest", r"testcontainers", r"WebTestClient",
        r"with_database", r"connects? to database", r"httpclient", r"mock server",

        # Python
        r"django.test", r"flask_testing", r"live_server",
        # JS/TS
        r"supertest", r"msw", r"axios", r"cy.request",
        # Go
        r"httptest", r"sqlmock", r"gorm", r"database/sql",
        # PHP
        r"Laravel\\", r"Mockery",
        # .NET
        r"[TestServer]", r"InMemoryDatabase",
    ],

    "e2e": [
        # === General ===
        r"selenium", r"cypress", r"puppeteer", r"playwright",
        r"end-to-end", r"e2e", r"@E2ETest",

        # Android / Flutter
        r"androidx\.test", r"Espresso", r"UiAutomator",
        r"flutter_test", r"integration_test",

        # Web (JS)
        r"cy.visit", r"page.goto", r"browser.newPage",
        # Python
        r"from\s+selenium", r"behave", r"robotframework",
        # .NET
        r"SpecFlow", r"[Binding]",
    ]
}

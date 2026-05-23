
   #include <stdio.h>
#include <string.h>
int language;
typedef struct {

    char drug1[50];
    char drug2[50];
    char severity[20];
    char warning[200];

} Interaction;
Interaction interactionDB[] = {

    {
        "Aspirin",
        "Warfarin",
        "HIGH",
        "Severe bleeding risk detected."
    },

    {
        "Paracetamol",
        "Warfarin",
        "MEDIUM",
        "Liver complications possible."
    },

    {
        "Ibuprofen",
        "Aspirin",
        "HIGH",
        "Stomach bleeding risk."
    },

    {
        "Cetirizine",
        "Alcohol",
        "MEDIUM",
        "Drowsiness may increase."
    }
};

int totalInteractions = 4;
void selectLanguage() {

    printf("====================================\n");
    printf(" SELECT LANGUAGE\n");
    printf("====================================\n");

    printf("1. English\n");
    printf("2. Hindi\n");
    printf("3. Bengali\n");
    printf("4. Tamil\n");
    printf("5. Telugu\n");

    printf("\nEnter choice: ");
    scanf("%d", &language);
}
void displayWelcome() {

    if(language == 1) {

        printf("\nDRUG INTERACTION WARNING SYSTEM\n");
    }

    else if(language == 2) {

        printf("\nदवा इंटरैक्शन चेतावनी प्रणाली\n");
    }

    else if(language == 3) {

        printf("\nওষুধ ইন্টারঅ্যাকশন সতর্কীকরণ সিস্টেম\n");
    }

    else if(language == 4) {

        printf("\nமருந்து தொடர்பு எச்சரிக்கை அமைப்பு\n");
    }

    else if(language == 5) {

        printf("\nఔషధ పరస్పర చర్య హెచ్చరిక వ్యవస్థ\n");
    }
}

void displayInputMethod() {

    if(language == 1) {

        printf("\n1. Upload Image From Gallery\n");
        printf("2. Manual Medicine Entry\n");
    }

    else if(language == 2) {

        printf("\n1. गैलरी से इमेज अपलोड करें\n");
        printf("2. दवा का नाम दर्ज करें\n");
    }

    else if(language == 3) {

        printf("\n1. গ্যালারি থেকে ছবি আপলোড করুন\n");
        printf("2. ওষুধের নাম লিখুন\n");
    }

    else if(language == 4) {

        printf("\n1. கேலரியில் இருந்து படத்தை பதிவேற்றுக\n");
        printf("2. மருந்து பெயரை உள்ளிடுக\n");
    }

    else if(language == 5) {

        printf("\n1. గ్యాలరీ నుండి చిత్రాన్ని అప్లోడ్ చేయండి\n");
        printf("2. మందుల పేర్లు నమోదు చేయండి\n");
    }
}

void displayDangerWarning() {

    if(language == 1) {

        printf("\nWARNING: Dangerous Drug Interaction Detected!\n");
    }

    else if(language == 2) {

        printf("\nचेतावनी: खतरनाक दवा इंटरैक्शन मिला!\n");
    }

    else if(language == 3) {

        printf("\nসতর্কতা: বিপজ্জনক ওষুধ প্রতিক্রিয়া সনাক্ত হয়েছে!\n");
    }

    else if(language == 4) {

        printf("\nஎச்சரிக்கை: ஆபத்தான மருந்து தொடர்பு கண்டறியப்பட்டது!\n");
    }

    else if(language == 5) {

        printf("\nహెచ్చరిక: ప్రమాదకర ఔషధ పరస్పర చర్య గుర్తించబడింది!\n");
    }
}

void displaySafeMessage() {

    if(language == 1) {

        printf("\nNo dangerous interactions found.\n");
    }

    else if(language == 2) {

        printf("\nकोई खतरनाक इंटरैक्शन नहीं मिला।\n");
    }

    else if(language == 3) {

        printf("\nকোনও বিপজ্জনক প্রতিক্রিয়া পাওয়া যায়নি।\n");
    }

    else if(language == 4) {

        printf("\nஆபத்தான தொடர்புகள் எதுவும் இல்லை.\n");
    }

    else if(language == 5) {

        printf("\nప్రమాదకర పరస్పర చర్యలు కనబడలేదు.\n");
    }
}
void inputMedicines(char medicines[][50], int *count) {

    printf("\nEnter number of medicines: ");
    scanf("%d", count);

    for(int i = 0; i < *count; i++) {

        printf("Enter medicine %d: ", i + 1);
        scanf("%s", medicines[i]);
    }
}
void performOCR(char imagePath[],
                char medicines[][50],
                int *count) {

    printf("\n[OCR] Processing Image: %s\n", imagePath);

    printf("\nEnter medicines detected from image:\n");

    inputMedicines(medicines, count);
}
void checkInteractions(char medicines[][50], int count) {

    int found = 0;

    for(int i = 0; i < count; i++) {

        for(int j = i + 1; j < count; j++) {

            for(int k = 0; k < totalInteractions; k++) {

                if(

                    (
                        strcmp(medicines[i],
                               interactionDB[k].drug1) == 0

                        &&

                        strcmp(medicines[j],
                               interactionDB[k].drug2) == 0
                    )

                    ||

                    (
                        strcmp(medicines[j],
                               interactionDB[k].drug1) == 0

                        &&

                        strcmp(medicines[i],
                               interactionDB[k].drug2) == 0
                    )
                  )

                {

                    found = 1;

                    printf("\n====================================");

                    displayDangerWarning();

                    printf("====================================");

                    printf("\nDrugs     : %s + %s",
                           medicines[i],
                           medicines[j]);

                    printf("\nSeverity  : %s",
                           interactionDB[k].severity);

                    printf("\nWarning   : %s\n",
                           interactionDB[k].warning);
                }
            }
        }
    }

    if(found == 0) {

        displaySafeMessage();
    }
}
int main() {

    char medicines[10][50];
    int count = 0;
    int choice;

    selectLanguage();

    printf("\n====================================\n");

    displayWelcome();

    printf("====================================\n");

    displayInputMethod();

    printf("\nEnter choice: ");
    scanf("%d", &choice);

    if(choice == 1) {

        printf("\n[INFO] Simulating Gallery Image Upload...\n");

        performOCR("pill_image.jpg",
                   medicines,
                   &count);
    }

    else if(choice == 2) {

        printf("\n[INFO] Manual Medicine Entry Selected\n");

        inputMedicines(medicines,
                       &count);
    }

    else {

        printf("\nInvalid Choice!\n");
        return 0;
    }
    printf("\nDetected Medicines:\n");

    for(int i = 0; i < count; i++) {

        printf("- %s\n", medicines[i]);
    }
    printf("\nChecking Drug Interactions...\n");

    checkInteractions(medicines,
                      count);

    printf("\n====================================");
    printf("\nSystem Scan Completed");
    printf("\n====================================\n");

    return 0;
}

#include <stdio.h>
#include <string.h>
#include <ctype.h>

#define MAX_MEDICINES 10
#define MAX_NAME_LEN 50

typedef struct {

    char drug1[MAX_NAME_LEN];
    char drug2[MAX_NAME_LEN];
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
    }
};

int totalInteractions = 3;


void toLowerCase(char str[]) {

    for(int i = 0; str[i]; i++) {

        str[i] = tolower(str[i]);
    }
}

int compareIgnoreCase(char a[], char b[]) {

    char str1[MAX_NAME_LEN];
    char str2[MAX_NAME_LEN];

    strcpy(str1, a);
    strcpy(str2, b);

    toLowerCase(str1);
    toLowerCase(str2);

    return strcmp(str1, str2);
}


void inputMedicines(char medicines[][MAX_NAME_LEN], int *count) {

    printf("\nEnter number of medicines (1-%d): ", MAX_MEDICINES);
    scanf("%d", count);

    getchar(); // remove newline

    if(*count <= 0 || *count > MAX_MEDICINES) {

        printf("\nInvalid number of medicines.\n");
        *count = 0;
        return;
    }

    for(int i = 0; i < *count; i++) {

        printf("Enter medicine %d: ", i + 1);

        fgets(medicines[i], MAX_NAME_LEN, stdin);

        medicines[i][strcspn(medicines[i], "\n")] = '\0';
    }
}

void performOCR(char imagePath[],
                char medicines[][MAX_NAME_LEN],
                int *count) {

    printf("\n[OCR] Processing Image: %s\n", imagePath);

    printf("\nEnter medicines detected from image:\n");

    inputMedicines(medicines, count);
}

void checkInteractions(char medicines[][MAX_NAME_LEN], int count) {

    int found = 0;

    for(int i = 0; i < count; i++) {

        for(int j = i + 1; j < count; j++) {

            for(int k = 0; k < totalInteractions; k++) {

                if(

                    (
                        compareIgnoreCase(
                            medicines[i],
                            interactionDB[k].drug1
                        ) == 0

                        &&

                        compareIgnoreCase(
                            medicines[j],
                            interactionDB[k].drug2
                        ) == 0
                    )

                    ||

                    (
                        compareIgnoreCase(
                            medicines[j],
                            interactionDB[k].drug1
                        ) == 0

                        &&

                        compareIgnoreCase(
                            medicines[i],
                            interactionDB[k].drug2
                        ) == 0
                    )
                )

                {

                    found = 1;

                    printf("\n====================================");
                    printf("\nINTERACTION DETECTED");
                    printf("\n====================================");

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

        printf("\nNo dangerous interactions found.\n");
    }
}

int main() {

    char medicines[MAX_MEDICINES][MAX_NAME_LEN];
    int count = 0;

    printf("====================================\n");
    printf(" DRUG INTERACTION WARNING SYSTEM\n");
    printf("====================================\n");

    printf("\nSelect Input Method:\n");
    printf("1. Upload Image From Gallery\n");
    printf("2. Manual Medicine Entry\n");

    int choice;

    printf("\nEnter choice: ");
    scanf("%d", &choice);

    getchar(); 

    if(choice == 1) {

        printf("\n[INFO] Simulating Gallery Image Upload...\n");

        performOCR(
            "pill_image.jpg",
            medicines,
            &count
        );
    }

    else if(choice == 2) {

        printf("\n[INFO] Manual Medicine Entry Selected\n");

        inputMedicines(medicines, &count);
    }

    else {

        printf("\nInvalid Choice!\n");
        return 0;
    }

    if(count == 0) {

        return 0;
    }

    printf("\nDetected Medicines:\n");

    for(int i = 0; i < count; i++) {

        printf("- %s\n", medicines[i]);
    }

    printf("\nChecking Drug Interactions...\n");

    checkInteractions(medicines, count);

    printf("\n====================================");
    printf("\nSystem Scan Completed");
    printf("\n====================================\n");

    return 0;
}

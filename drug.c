#include <stdio.h>
#include <string.h>

int main() {

    char language[20];
    char medicine1[50];
    char medicine2[50];

    printf("=====================================\n");
    printf("       MEDPLUS SYSTEM\n");
    printf(" Drug Interaction Warning System\n");
    printf("=====================================\n\n");

    /* Language Selection */

    printf("Select Language:\n");
    printf("1. English\n");
    printf("2. Hindi\n");
    printf("3. Bengali\n");
    printf("4. Tamil\n");
    printf("5. Telugu\n\n");

    printf("Enter Language: ");
    scanf("%s", language);

    printf("\nLanguage Selected: %s\n", language);

    /* Medicine Scan Section */

    printf("\n--- Scan Pill Bottle ---\n");

    printf("Enter First Medicine Name: ");
    scanf("%s", medicine1);

    printf("Enter Second Medicine Name: ");
    scanf("%s", medicine2);

    /* Display Medicines */

    printf("\nDetected Medicines:\n");
    printf("1. %s\n", medicine1);
    printf("2. %s\n", medicine2);

    /* Drug Interaction Checking */

    if ((strcmp(medicine1, "Warfarin") == 0 &&
         strcmp(medicine2, "Aspirin") == 0) ||

        (strcmp(medicine1, "Aspirin") == 0 &&
         strcmp(medicine2, "Warfarin") == 0)) {

        printf("\n=====================================\n");
        printf(" SEVERE INTERACTION WARNING!\n");
        printf(" Warfarin and Aspirin may increase\n");
        printf(" the risk of bleeding.\n");
        printf(" Consult your doctor immediately.\n");
        printf("=====================================\n");
    }

    else if ((strcmp(medicine1, "Paracetamol") == 0 &&
              strcmp(medicine2, "Ibuprofen") == 0) ||

             (strcmp(medicine1, "Ibuprofen") == 0 &&
              strcmp(medicine2, "Paracetamol") == 0)) {

        printf("\nWarning: Use medicines carefully.\n");
    }

    else {

        printf("\nNo Severe Drug Interaction Found.\n");
    }

    printf("\nThank You For Using MedPlus.\n");

    return 0;
}

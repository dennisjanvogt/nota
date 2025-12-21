"""
Forms für E-Mail-Verwaltung.
"""
from django import forms
from .models import EmailVorlage


class EmailVorlageForm(forms.ModelForm):
    """Form für E-Mail-Vorlagen."""

    class Meta:
        model = EmailVorlage
        fields = [
            'name',
            'workflow_typ',
            'kategorie',
            'betreff',
            'nachricht',
            'standard_empfaenger',
            'cc_empfaenger',
            'ist_aktiv',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Anfrage Strafregisterauszug'
            }),
            'workflow_typ': forms.Select(attrs={'class': 'form-control'}),
            'kategorie': forms.Select(attrs={'class': 'form-control'}),
            'betreff': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'z.B. Anfrage Strafregisterauszug - {nachname}'
            }),
            'nachricht': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Sehr geehrte Damen und Herren,...'
            }),
            'standard_empfaenger': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'beispiel@justiz.gv.at'
            }),
            'cc_empfaenger': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'mehrere@example.com, adressen@example.com'
            }),
            'ist_aktiv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EmailSendenForm(forms.Form):
    """Form zum Versenden einer E-Mail basierend auf Vorlage."""

    empfaenger = forms.EmailField(
        label='Empfänger',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'empfaenger@example.com'
        })
    )

    cc_empfaenger = forms.CharField(
        label='CC',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional: cc1@example.com, cc2@example.com'
        }),
        help_text='Mehrere E-Mail-Adressen mit Komma trennen'
    )

    betreff = forms.CharField(
        label='Betreff',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )

    nachricht = forms.CharField(
        label='Nachricht',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 12
        })
    )

    def clean_cc_empfaenger(self):
        """Validiere CC-Empfänger."""
        cc = self.cleaned_data.get('cc_empfaenger', '').strip()
        if not cc:
            return ''

        # Split by comma and validate each email
        emails = [e.strip() for e in cc.split(',') if e.strip()]
        for email in emails:
            try:
                forms.EmailField().clean(email)
            except forms.ValidationError:
                raise forms.ValidationError(f'Ungültige E-Mail-Adresse: {email}')

        return ', '.join(emails)
